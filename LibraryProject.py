from flask import Flask, render_template, request, session, flash, jsonify, abort, redirect, url_for

import sqlite3 as sql
import math
import re
from markupsafe import escape
import os  # package used to generate random number
import socket
import Encryption
import pandas as pd
import hmac, hashlib


key = b'\x89\xcc\x01y\xfd\xbd\xcd=Gv\x99m\xa5\x9f?f\x02\x86\xc9#\xea\xf7\xc3e\xd6\xa0\t\x06D\xad<\x84'
iv = b'w\xdb^K%\\\xf5,`\xc7\xbb\xabs\x1f\x06\x16'
cipher = Encryption.AESCipher(key,iv)

def create_app() -> Flask:
   app = Flask(__name__)
   ...
   return app
# initialization of flask object
app = Flask(__name__)


# Reading in the API Key for Google Maps
def get_google_maps_api_key():
    with open('GMAPS_KEY.txt', 'r') as file:
        return file.read().strip()

GOOGLE_MAPS_API_KEY = get_google_maps_api_key()


# December 3rd - Isaias Quintero
# Google Maps integration and library location coordinates
# Any other locations would be added manually, and though this isn't as efficient, it's what works right now
@app.route('/libraryCoordinates', methods=['GET'])
def get_library_coordinates():
    libraries = {
        'Florida Bay County Library': {'lat': 30.168766402005918, 'lng': -85.67267684156133},
        'Homestead Public Library': {'lat': 25.475735637116777, 'lng': -80.46685750928418},
        'Key Largo Library': {'lat': 25.11286993925325, 'lng': -80.41979818982614},
        'Everglades City Library': {'lat': 25.857969187716723, 'lng': -81.38449944562407},
    }
    return jsonify(libraries)



# definition of home page, return home.html
@app.route('/')
def home():
    if not session.get('logged_in'):   # if user not logged in and tries to access this page, redirect to login
        return render_template('login.html')
    # Logic to handle case where library gets deleted. Directs user to enter new library
    elif session.get('UserLocalLibraryName') == -1:
        return render_template('changeLibrary.html')
    else:
        return render_template('home.html', name=session['name'], UserLocalLibrary=session['UserLocalLibraryName'])
    # October 16th merge update:
    # render_template() updated so session['UserLocalLibraryName'] is passed in instead.
    # Notice the 'Name' at the end. Change explained later in file.
    # Changed by Pablo

# definition of create account, return createAccount.html
@app.route('/createAccount')
def create_account():
    return render_template('createAccount.html')

# definition of list borrowed materials, return loans.html
# October 27th update - Shawnie Houston
# Added the logic to display the user's currently borrow materials

# November 3rd update - Josh Knorr
# Changed how a user's checked out books are searched for - searches for user name match vs library match

@app.route('/loans')
def loans():
    if not session.get('logged_in'):   # if user not logged in and tries to access this page, redirect to login
        return render_template('login.html')
    else:
        con = sql.connect("Library.db")
        con.row_factory = sql.Row
        cur = con.cursor()
        user_logon = session['username']

        # get book name, checked out date, and return by date of logged in user's books
        sql_query = '''SELECT b.bookName, lo.checkedOut, lo.returnBy, lib.libraryName \
                        FROM Loans lo
                        JOIN Books b ON b.bookID = lo.bookID
                        JOIN Libraries lib ON lib.libraryID = b.libraryID
                        WHERE lo.userLogon = ?;'''

        cur.execute(sql_query, (user_logon,))

        df = pd.DataFrame(cur.fetchall(), columns=['b.bookName', 'lo.checkedOut', 'lo.returnBy','lib.libraryName'])
        return render_template("loans.html", rows = df)


# definition of showUser, return show.html
@app.route('/showUser')
def show_user():
    if not session.get('logged_in'):   # if user not logged in and tries to access this page, redirect to login
        return render_template('login.html')
    else:  # open conenction to sql table to display info about logged in user
        con = sql.connect("Library.db")
        con.row_factory = sql.Row
        cur = con.cursor()

        # October 16th merge update:
        # Select query updated. It now joins the LibUsers and Libraries tables based on Library ID in order to fetch
        # the current user's local library name. It also selects first name and last name separately, but they're joined
        # together in show.html. Tried to emulate the initial version as closely as possible with the new schemas.
        # Changed by Pablo
        sql_select_query = """select firstName,lastName,phoneNum,userAddress,Libraries.libraryName,securityLevel,password
                              from LibUsers 
                              join Libraries on LibUsers.libraryID = Libraries.libraryID
                              where userLogon = ?"""
        cur.execute(sql_select_query, [session['username']])
        df = pd.DataFrame(cur.fetchall(),
                          columns=['firstName', 'lastName', 'phoneNum', 'userAddress', 'Libraries.libraryName', 'securityLevel',
                                   'password']);

        # first name
        df.iat[0, 0] = cipher.decrypt(df.iat[0, 0])
        # last name
        df.iat[0, 1] = cipher.decrypt(df.iat[0, 1])
        # UserPhNum
        df.iat[0, 2] = cipher.decrypt(df.iat[0, 2])
        # UserAddress
        df.iat[0, 3] = cipher.decrypt(df.iat[0, 3])
        # LoginPassword
        df.iat[0, 6] = cipher.decrypt(df.iat[0, 6])

        # Checks to see if the user currently logged in already made a request to upgrade their security level
        # If they have, update the requestExists flag to True, which will prevent the link to the form from displaying
        # This is to ensure users can't spam requests. There can only be one request per user ID
        # October 16th merge update: Select query tweaked so UserLogon is selected instead of UserId. Changed by Pablo
        requestExists = False
        cur.execute(f"SELECT UserLogon FROM UpgradeReqs WHERE UserLogon = '{session.get('username')}'")
        if cur.fetchone() is not None:
            requestExists = True

        return render_template("show.html", row = df, requestExists = requestExists)


# definition of add rec, when user.html is called, this function is called
@app.route('/addrec', methods=['POST', 'GET'])
def addrec():

    if request.method == 'POST':

        # October 16th merge update:
        # Extra fields have been included and received from the account creation page.
        # Changed by Pablo.
        usrnm = request.form['UserName']
        fnm = request.form['FirstName']
        lnm = request.form['LastName']
        ph = request.form['PhoneNumber']
        ad = request.form['Address']
        cty = request.form['City']
        st = request.form['State']
        zip = request.form['Zip']
        ll = request.form.get('selectedLibrary')
        pwd = request.form['Password']

        usrnm = str(usrnm).strip()  # removes whitespace
        fnm = str(fnm).strip()  # removes whitespace
        lnm = str(lnm).strip()  # removes whitespace
        ph = str(ph).strip()  # removes whitespace
        ad = str(ad).strip()  # removes whitespace
        cty = str(cty).strip()  # removes whitespace
        st = str(st).strip()  # removes whitespace
        zip = str(zip).strip()  # removes whitespace
        ll = str(ll).strip()  # removes whitespace
        pwd = str(pwd).strip()  # removes whitespace

        message = ""  # initialization of blank string for error message
        errors = 0  # initialization of error counter

# if statements to catch blank inputs
        if (len(usrnm) == 0):
            message = message + "Can not create account, Username is required\n"
            errors += 1
        if (len(fnm) == 0):
            message = message + "Can not create account, First Name is required\n"
            errors += 1
        if (len(lnm) == 0):
            message = message + "Can not create account, Last Name is required\n"
            errors += 1
        if (len(ph)==0):
            message = message + "Can not create account, Phone Number is required\n"
            errors += 1
        if (len(ad)==0):
            message = message + "Can not create account, Address is required\n"
            errors += 1
        if (len(cty)==0):
            message = message + "Can not create account, City is required\n"
            errors += 1
        if (len(st)==0):
            message = message + "Can not create account, State is required\n"
            errors += 1
        if (len(zip)==0):
            message = message + "Can not create account, Zip code is required\n"
            errors += 1
        if (len(ll)==0):
            message = message + "Can not create account, Local Library is required\n"
            errors += 1
        if (len(pwd) == 0):
            message = message + "Can not create account, password is required\n"
            errors += 1
        if (errors > 0):   # if error counter > 0, display all error messages generated
            message = message.split('\n')
            return render_template("result.html", msg=message)

        else:  # if no error messages, attempt connection with db
            # try except finally block to attempt database connection and update of records
            try:

                with sql.connect("Library.db") as con:
                    cur = con.cursor()

                    fnm = cipher.encrypt(fnm)
                    lnm = cipher.encrypt(lnm)
                    ph = cipher.encrypt(ph)
                    ad = cipher.encrypt(ad)
                    cty = cipher.encrypt(cty)
                    st = cipher.encrypt(st)
                    zip = cipher.encrypt(zip)
                    pwd = cipher.encrypt(pwd)

                    # October 16th merge update:
                    # Due to table schemas changing drastically, local library choosing needs to be handled differently.
                    # Goes to the Libraries table and checks if the user inputted a library that exists in the table.
                    # If it does, assign the user's library ID to the one in the record found.
                    # If not, display an error that the library doesn't exist in the database. Normally I'd make it so
                    # the library would just be created as a new record, but I realized this will be a feature only
                    # existing level 3 users can do, so I skipped out on it.
                    # Changed by Pablo.
                    cur.execute(f"SELECT libraryID FROM Libraries WHERE libraryName = '{ll}'")
                    result = cur.fetchone()
                    if result:
                        libId = result[0]
                    else:
                        message = message + "Can not create account, local library entered does not exist in database\n"
                        return render_template("result.html", msg=message)

                    # Functionality to add user to table has changed
                    # New users' security level is 1 by default, they can't choose anymore
                    # Minor change by Pablo

                    # October 16th merge update:
                    # Changed insert query to include all extra fields in the LibUsers table.
                    # Changed by Pablo.
                    cur.execute("INSERT INTO LibUsers (userLogon,"
                                "libraryID,"
                                "firstName,"
                                "lastName,"
                                "phoneNum,"
                                "userAddress,"
                                "userCity,"
                                "userState,"
                                "userZip,"
                                "securityLevel,"
                                "password) "
                                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",(usrnm, libId, fnm, lnm, ph, ad, cty, st, zip, 1, pwd))

                    con.commit()
                    message = message + "Account successfully created\n"

            except Exception as e:
                con.rollback()
                print(f"Error: {e}")
                message = message + "error in insert operation\n" + f"Error: {e}"

            finally:
                message = message.split('\n')
                return render_template("result.html", msg=message)
                con.close()

# if view list link clicked from home page, executes below function
# Update: The "User who checked out the book" column in the displayed table no longer displays encrypted values
# Updated by Pablo

# November 15th, 2024 - Shawnie
# Removed single quotes around b.bookID in SELECT query for level 3 user
@app.route('/list')
def list():
    if not session.get('logged_in'):   # if user not logged in and tries to access this page, redirect to login
        return render_template('login.html')
    elif session.get('admin') == 2:  # checks if user security level is 2
        con = sql.connect("Library.db")
        con.row_factory = sql.Row
        cur = con.cursor()
        ul = session['UserLocalLibrary']


        # October 16th merge update:
        # Updated select queries to account for changes in table schemas.
        # Aimed to make the result as close as possible to Joshua's initial code results, but I may have gotten it wrong.
        # Further testing necessary.
        # Changed by Pablo.
        #
        # October 27th - Shawnie Houston
        # Updated SQL query so the FROM is for loans and it's searching based on Books' libraryID
        # Previous query was returning wrong library
        sql_query = '''SELECT b.bookName, u.firstName, u.lastName, lib.libraryName, lo.checkedOut, lo.returnBy, b.bookID \
                FROM Loans lo
                JOIN LibUsers u ON u.userLogon = lo.userLogon
                JOIN Books b ON b.bookID = lo.bookID
                JOIN Libraries lib ON lib.libraryID = b.libraryID
                WHERE b.libraryID = ?;'''
        cur.fetchall()
        cur.execute(sql_query, (ul,))

        df = pd.DataFrame(cur.fetchall(), columns=['b.bookName', 'u.firstName', 'u.lastName', 'lib.libraryName', 'lo.checkedOut', 'lo.returnBy', 'b.bookID'])
        df['u.firstName'] = df['u.firstName'].apply(lambda x: cipher.decrypt(x)) # Decrypts user's first name
        df['u.lastName'] = df['u.lastName'].apply(lambda x: cipher.decrypt(x)) # Decrypts user's last name
        return render_template("list.html", rows = df)

    elif session.get('admin') == 3:  # checks if user security level is 3
        con = sql.connect("Library.db")
        con.row_factory = sql.Row
        cur = con.cursor()
        ul = session['UserLocalLibrary']


        # October 16th merge update:
        # Updated select queries to account for changes in table schemas.
        # Aimed to make the result as close as possible to Joshua's initial code results, but I may have gotten it wrong.
        # Further testing necessary.
        # Changed by Pablo.
        #
        # October 27th - Shawnie Houston
        # Updated SQL query so the FROM is for loans, and it's searching based on Books' libraryID
        sql_query = '''SELECT b.bookName, u.firstName, u.lastName, lib.libraryName, lo.checkedOut, lo.returnBy,b.bookID \
                FROM Loans lo
                JOIN LibUsers u ON u.userLogon = lo.userLogon
                JOIN Books b ON b.bookID = lo.bookID
                JOIN Libraries lib ON lib.libraryID = b.libraryID;'''
        cur.fetchall()
        cur.execute(sql_query)

        df = pd.DataFrame(cur.fetchall(), columns=['b.bookName', 'u.firstName', 'u.lastName', 'lib.libraryName', 'lo.checkedOut', 'lo.returnBy','b.bookID'])
        df['u.firstName'] = df['u.firstName'].apply(lambda x: cipher.decrypt(x)) # Decrypts user's first name
        df['u.lastName'] = df['u.lastName'].apply(lambda x: cipher.decrypt(x)) # Decrypts user's last name
        return render_template("list.html", rows = df)
    else:
        abort(404)  # if user does not have high enough security level, return 404 error

# October 16th merge update:
# Login is handled differently due to changes in other functions. More details in comments inside the function.
# Changed by Pablo.
@app.route('/login', methods=['POST'])
def do_admin_login():

   try:
      usrnm = request.form['username']  # reads in inputted username and password from login.html
      pwd = request.form['password']
      with sql.connect("Library.db") as con:
         con.row_factory = sql.Row
         cur = con.cursor()

         # Username encryption removed, as this is what's used as LibUsers's primary key now.
         pwd = cipher.encrypt(pwd)  # encrypts pwd to match to encrypted form in table

         # tries to match username and password to entry in table
         sql_select_query = """select * from LibUsers where userLogon = ? and password = ?"""
         cur.execute(sql_select_query, (usrnm,pwd))

         row = cur.fetchone();
         if (row != None):  # this is true if a record is found
            session['logged_in'] = True  # if log in successful, set logged_in to true
            session['username'] = usrnm  # sets session['username'] to name entered as username in log in field

            # Sets the user's DISPLAY name as a concatenation of their decrypted first and last names.
            session['name'] = cipher.decrypt(row['firstName']) + " " + cipher.decrypt(row['lastName'])

            # session['UserLocalLibrary'] is now an integer ID variable, not a string anymore. However, some functions
            # or HTML files still handle 'UserLocalLibrary' as a string of text. To handle this, a new session variable
            # is created: session['UserLocalLibraryName']
            session['UserLocalLibrary'] = row['libraryID']

            # Checks if there's a record in the Libraries table with the user's library ID
            # If there is, assign its name to session['UserLocalLibraryName']. This is what home() was using earlier.
            cur.execute(f"SELECT libraryName FROM Libraries WHERE libraryID = {row['libraryID']}")
            row2 = cur.fetchone()
            if (row2 != None):
                session['UserLocalLibraryName'] = row2['libraryName']
            # Handles deleted libraries
            else:
                session['UserLocalLibraryName'] = -1

            # below if statements to set users security level, which is held in the session['admin'] variable
            # this comes from sql table
            if (int(row['securityLevel'])==3):
               session['admin'] = 3
            elif(int(row['securityLevel'])==2):
               session['admin'] = 2
            else:
               session['admin'] = 1

         else:  # if either username or password are invalid, returns message
            session['logged_in'] = False
            flash('invalid username and/or password!')
   except:
      con.rollback()
      flash("error in insert operation")
   finally:
      con.close()
   return home()



# ---------------------------------------------------------------------------------------------------
# --- Pablo's Code: Security level upgrade functionality --------------------------------------------
# --- Four new Flask functions: requestUpgrade(), addRequest(), listRequests(), and upgradeUser() ---
# --- Two new HTML files: showRequests.html and requestUpgrade.html ----------------------------------
# --- One new SQLite table: UpgradeReqs. Schema shown in project tracking spreadsheet ---------------
# --- Minor changes to the show_user(), list(), and addrec() functions ------------------------------
# --- Minor changes to the show.html, home.html, and createAccount.html files ------------------------
# --- Added UpgradeReqs table to LibraryCreateDB.py file ---------------------------------------------
# ---------------------------------------------------------------------------------------------------

# October 16th merge update:
# Minor changes to my functions to account for new table schemas.
# Changed by Pablo.

# Displays the page containing the form users will fill out to request an
# upgrade to their security level
@app.route('/request')
def requestUpgrade():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('requestUpgrade.html')

# Receives the data the user sent in their form and adds it to the UpgradeReqs table
@app.route('/requestSent', methods=['POST', 'GET'])
def addRequest():
    if not session.get('logged_in'):
        return render_template('login.html')
    elif request.method == 'POST':
        # Values obtained by the current user's session
        usrnm = session.get('username')
        name = cipher.encrypt(session.get('name'))
        currlvl = session.get('admin')

        reason = request.form['Reason']
        tasks = request.form['Tasks']

        # If the user was a level 2, no desired level choice was made, so the desired level will be 3 by default
        # Otherwise, it'll depend on the user's choice
        deslvl = request.form.get('levelChoice')
        if deslvl is None:
            deslvl = 3
        else:
            deslvl = int(deslvl)

        # Depending on the user's current level or level choice, there may be one experience field that's not filled out
        # This code handles the 3 possible scenarios to prevent errors
        if currlvl == 1 and deslvl == 2:
            invExp = cipher.encrypt(request.form['InvExperience'])
            netExp = cipher.encrypt("User chose to upgrade to level 2.")
        elif currlvl == 1 and deslvl == 3:
            invExp = cipher.encrypt(request.form['InvExperience'])
            netExp = cipher.encrypt(request.form['NetExperience'])
        else:
            invExp = cipher.encrypt("Already managing LitManager's inventories as a level 2 administrator.")
            netExp = cipher.encrypt(request.form['NetExperience'])

        # Try except finally block to add a user's request to the table
        try:
            with sql.connect("Library.db") as con:
                cur = con.cursor()
                cur.execute("INSERT INTO UpgradeReqs (UserLogon,"
                            "UserName,"
                            "CurrentLevel,"
                            "DesiredLevel,"
                            "Reason,"
                            "InvExperience,"
                            "NetExperience,"
                            "Tasks) "
                            "VALUES (?,?,?,?,?,?,?,?)", (usrnm, name, currlvl, deslvl, reason, invExp, netExp, tasks))
                con.commit()
        except Exception as e:
            con.rollback()
            print(f"Error: {e}")
            print("Error in insert operation\n" + f"Error: {e}")
            return redirect(url_for('requestUpgrade'))
        finally:
            con.close()
            flash("Request sent successfully!")
            return redirect(url_for('show_user'))
    else:
        print("An error occurred...")
        flash("An error occurred...")
        return redirect(url_for('requestUpgrade'))

# Displays a list of all user upgrade requests that only level 3 users can view
@app.route('/requestList')
def listRequests():
    if not session.get('logged_in'):
        return render_template('login.html')

    # Redirects the current user back to the home page if their security level is not high enough
    elif session.get('admin') < 3:
        flash("You must have security level 3 to access this page...")
        return render_template('home.html')

    else:
        con = sql.connect("Library.db")
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM UpgradeReqs")

        df = pd.DataFrame(cur.fetchall(), columns=['RequestId', 'UserLogon', 'UserName', 'CurrentLevel', 'DesiredLevel', 'DateOfRequest', 'Reason', 'InvExperience', 'NetExperience', 'Tasks'])
        df['UserName'] = df['UserName'].apply(lambda x: cipher.decrypt(x))
        df['InvExperience'] = df['InvExperience'].apply(lambda x: cipher.decrypt(x))
        df['NetExperience'] = df['NetExperience'].apply(lambda x: cipher.decrypt(x))

        return render_template('showRequests.html', rows = df)

# Handles the acceptance or rejection of requests
# They are handled based on unique User IDs, as opposed to usernames
# This ensures users sharing the same name won't be affected
@app.route('/upgrade')
def upgradeUser():
    if not session.get('logged_in'):
        return render_template('login.html')

    # Redirects the current user back to the home page if their security level is not high enough
    elif session.get('admin') < 3:
        flash("You must have security level 3 to access this page...")
        return render_template('home.html')

    else:
        # GET arguments taken from the "Accept" and "Reject" hyperlinks in the showRequests.html file
        id = request.args.get('id', default="", type=str)
        reqID = request.args.get('reqID', default=-1, type=int)
        lvl = request.args.get('level', default=-1, type=int)
        accepted = request.args.get('accept', default="false").lower() == "true"

        # If the user hit the "Accept" button, the chosen request is removed from UpgradeReqs
        # Additionally, the LibUsers table is updated so the user's security
        # level is updated to their chosen level
        if accepted:
            if id != "" and reqID != -1 and lvl != -1:
                # Try except finally block to update the LibUsers and UpgradeReqs tables
                try:
                    con = sql.connect("Library.db")
                    cur = con.cursor()
                    cur.execute(f"UPDATE LibUsers SET securityLevel={lvl} WHERE userLogon='{id}'")
                    cur.execute(f"DELETE FROM UpgradeReqs WHERE RequestId={reqID}")
                    con.commit()
                except Exception as e:
                    con.rollback()
                    print(f"Error: {e}")
                    print("Error in update and delete operations\n" + f"Error: {e}")
                    return redirect(url_for('listRequests'))
                finally:
                    con.close()
                    flash("User's security level successfully upgraded!")
                    return redirect(url_for('listRequests'))
            else:
                print("An error occurred accepting/rejecting the request...")
                flash("An error occurred accepting/rejecting the request...")
                return redirect(url_for('listRequests'))

        # If the user hit the "Reject" button, procedure is largely the same,
        # but the SQLite UPDATE statement is skipped, so the user's security
        # level is left intact.
        else:
            if id != "" and reqID != -1 and lvl != -1:
                # Try except finally block to update the UpgradeReqs table
                try:
                    con = sql.connect("Library.db")
                    cur = con.cursor()
                    cur.execute(f"DELETE FROM UpgradeReqs WHERE RequestId={reqID}")
                    con.commit()
                    con.close()
                except Exception as e:
                    con.rollback()
                    print(f"Error: {e}")
                    print("Error in delete operation\n" + f"Error: {e}")
                    return redirect(url_for('listRequests'))
                finally:
                    con.close()
                    flash("User's upgrade request successfully rejected...")
                    return redirect(url_for('listRequests'))
            else:
                print("An error occurred accepting/rejecting the request...")
                flash("An error occurred accepting/rejecting the request...")
                return redirect(url_for('listRequests'))

@app.route('/showLibs')
def showLibs():
    if not session.get('logged_in'):
        return render_template('login.html')

    elif session.get('admin') < 3:
        flash("You must have security level 3 to access this page...")
        return render_template('home.html')

    # Fetches library data to display them as a list in listLibraries.html
    else:
        con = sql.connect("Library.db")
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM Libraries")

        df = pd.DataFrame(cur.fetchall(), columns=['libraryID', 'libraryName', 'libraryAddress', 'libraryCity', 'libraryState', 'libraryZip'])
        return render_template('listLibraries.html', rows = df)

@app.route('/deleteLib')
def deleteLib():
    if not session.get('logged_in'):
        return render_template('login.html')

    elif session.get('admin') < 3:
        flash("You must have security level 3 to access this page...")
        return render_template('home.html')

    # Code is similar to upgradeUser() function
    else:
        libID = request.args.get('libID', default=-1, type=int)

        # -1 is the default value for a libraryID, set if obtaining an ID somehow failed
        if libID != -1:
            try:
                # If a valid ID was found, however, delete it
                con = sql.connect("Library.db")
                cur = con.cursor()
                cur.execute(f"DELETE FROM Libraries WHERE libraryID={libID}")
                con.commit()
            except Exception as e:
                con.rollback()
                print(f"Error: {e}")
                print("Error in delete operation\n" + f"Error: {e}")
                return redirect(url_for('showLibs'))
            finally:
                con.close()
                flash("Library successfully deleted!")
                return redirect(url_for('showLibs'))
        else:
            print("An error occurred deleting the library...")
            flash("An error occurred deleting the library...")
            return redirect(url_for('showLibs'))

@app.route('/addLibForm')
def addLibForm():
    if not session.get('logged_in'):
        return render_template('login.html')

    elif session.get('admin') < 3:
        flash("You must have security level 3 to access this page...")
        return render_template('home.html')

    # Redirects the user to a page where they can add a library with details of their choice
    else:
        return render_template('addLibrary.html')

@app.route('/addLib', methods=['POST', 'GET'])
def addLib():
    if not session.get('logged_in'):
        return render_template('login.html')

    elif session.get('admin') < 3:
        flash("You must have security level 3 to access this page...")
        return render_template('home.html')

    # Obtains data the user entered in addLibrary.html for a new library
    elif request.method == 'POST':
        nm = request.form['libName']
        ad = request.form['libAddress']
        cty = request.form['libCity']
        st = request.form['libState']
        zp = request.form['libZip']

        # Adds a new library to the database with this data
        try:
            with sql.connect("Library.db") as con:
                cur = con.cursor()
                cur.execute("INSERT INTO Libraries (libraryName,"
                            "libraryAddress,"
                            "libraryCity,"
                            "libraryState,"
                            "libraryZip)"
                            "VALUES (?,?,?,?,?)", (nm, ad, cty, st, zp))
                con.commit()
        except Exception as e:
            con.rollback()
            print(f"Error: {e}")
            print("Error in insert operation\n" + f"Error: {e}")
            return redirect(url_for('addLibForm'))
        finally:
            con.close()
            flash("Library successfully created! The Maps Visual will be confirmed manually by the head admin at a later date. Stay tuned!")
            return redirect(url_for('showLibs'))

    else:
        print("An error occurred...")
        flash("An error occurred...")
        return redirect(url_for('addLibForm'))

# ---------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------



# October 16th merge update:
# Added Shawnie's functions to implement search functionality into the website.
# Written by Shawnie, merged into main code by Pablo.

@app.route('/search')
# log in validation updated by Josh October 18th

def search():
    if not session.get('logged_in'):   # if user not logged in and tries to access this page, redirect to login
        return render_template('login.html')
    else:
        return render_template('search.html', name=session['name'], UserLocalLibrary=session['UserLocalLibraryName'])

# October 27th update - Shawnie Houston
# Changed function name and route to some form of "search results" to better distinguish between results and result
# Changed what users see based on security level. Standard and librarians will default see search results for their
# local library. Admins will see results for all libraries
# Still need to implement a way for standard users and librarians to be able to do a global search if they want
# to search more libraries.

# November 3rd Update - Josh Knorr
# added functionality to communicate with HTML page when a book is in loans table
# if this returns true, then the book will be unavailable for check out

@app.route('/searchResults', methods=['POST'])
def search_results():
    if request.method == 'POST':
        srch = request.form.get('libsearch')    # get search term
        cat = request.form.get('category')      # get category selected
        sec_lvl = session['admin']              # get security level
        un = session['username']                # get username

        # save search results for a user's global search
        session['srch'] = srch
        session['cat'] = cat

        # connect to db
        with sql.connect("Library.db") as con:
            con.row_factory = sql.Row
            cur = con.cursor()

            # if standard user or librarian
            if sec_lvl < 3:
                # if user wants to search books
                if cat == 'book':
                    # get data with username match and partial book name match
                    sql_query = '''SELECT b.bookID, b.bookName, b.author, b.description, b.genre, l.libraryName, b.dewey, \
                    CASE WHEN lo.bookID IS NULL THEN 1 ELSE 0 END AS available FROM Books b \
                    JOIN Libraries l ON l.libraryID = b.libraryID \
                    JOIN LibUsers u ON u.libraryID = l.libraryID \
                    LEFT JOIN Loans lo ON b.bookID = lo.bookID WHERE u.userLogon = ? \
                    AND b.bookName LIKE ?;'''
                    cur.fetchall()
                    cur.execute(sql_query, (un, '%'+srch+'%',))
                # if user wants to search by author
                elif cat == 'author':
                    # get data with username match and partial author name match
                    sql_query = '''SELECT b.bookID, b.bookName, b.author, b.description, b.genre, l.libraryName, b.dewey, \
                    CASE WHEN lo.bookID IS NULL THEN 1 ELSE 0 END AS available FROM Books b \
                    JOIN Libraries l ON l.libraryID = b.libraryID \
                    JOIN LibUsers u ON u.libraryID = l.libraryID \
                    LEFT JOIN Loans lo ON b.bookID = lo.bookID WHERE u.userLogon = ? \
                    AND b.author LIKE ?;'''
                    cur.fetchall()
                    cur.execute(sql_query, (un, '%'+srch+'%',))
                # if user wants to search by genre
                elif cat == 'genre':
                    # get data with username match and partial genre name match
                    sql_query = '''SELECT b.bookID, b.bookName, b.author, b.description, b.genre, l.libraryName, b.dewey, \
                    CASE WHEN lo.bookID IS NULL THEN 1 ELSE 0 END AS available FROM Books b \
                    JOIN Libraries l ON l.libraryID = b.libraryID \
                    JOIN LibUsers u ON u.libraryID = l.libraryID \
                    LEFT JOIN Loans lo ON b.bookID = lo.bookID WHERE u.userLogon = ? \
                    AND b.genre LIKE ?;'''
                    cur.fetchall()
                    cur.execute(sql_query, (un, '%'+srch+'%',))
            else:
                # if user wants to search by book
                if cat == 'book':
                    # return book name, author, description, genre, library name, and dewey decimal number
                    sql_query = '''SELECT b.bookID, b.bookName, b.author, b.description, b.genre, l.libraryName, b.dewey, \
                    CASE WHEN lo.bookID IS NULL THEN 1 ELSE 0 END AS available \
                    FROM Books b JOIN Libraries l ON b.libraryID = l.libraryID \
                    LEFT JOIN Loans lo ON b.bookID = lo.bookID WHERE b.bookName LIKE ?;'''
                    cur.fetchall()
                    cur.execute(sql_query, ('%' + srch + '%',))
                # if user wants to search by author
                elif cat == 'author':
                    # return book name, author, description, genre, library name, and dewey decimal number
                    sql_query = '''SELECT b.bookID, b.bookName, b.author, b.description, b.genre, l.libraryName, b.dewey, \
                    CASE WHEN lo.bookID IS NULL THEN 1 ELSE 0 END AS available \
                    FROM Books b JOIN Libraries l ON b.libraryID = l.libraryID \
                    LEFT JOIN Loans lo ON b.bookID = lo.bookID WHERE b.author LIKE ?;'''
                    cur.fetchall()
                    cur.execute(sql_query, ('%' + srch + '%',))
                # if user wants to search by genre
                elif cat == 'genre':
                    # return book name, author, description, genre, library name, and dewey decimal number
                    sql_query = '''SELECT b.bookID, b.bookName, b.author, b.description, b.genre, l.libraryName, b.dewey, \
                    CASE WHEN lo.bookID IS NULL THEN 1 ELSE 0 END AS available \
                    FROM Books b JOIN Libraries l ON b.libraryID = l.libraryID \
                    LEFT JOIN Loans lo ON b.bookID = lo.bookID WHERE b.genre LIKE ?;'''
                    cur.fetchall()
                    cur.execute(sql_query, ('%' + srch + '%',))
                # if user wants to search by library
                elif cat == 'library':
                    # return book name, author, description, genre, library name, and dewey decimal number
                    sql_query = '''SELECT b.bookID, b.bookName, b.author, b.description, b.genre, l.libraryName, b.dewey, \
                    CASE WHEN lo.bookID IS NULL THEN 1 ELSE 0 END AS available \
                    FROM Books b JOIN Libraries l ON b.libraryID = l.libraryID \
                    LEFT JOIN Loans lo ON b.bookID = lo.bookID WHERE l.libraryName LIKE ?;'''
                    cur.fetchall()
                    cur.execute(sql_query, ('%'+srch+'%',))
            # build data frame to send
            df = pd.DataFrame(cur.fetchall(), columns=['b.bookID','b.bookName', 'b.author', 'b.description', 'b.genre', 'l.libraryName', 'b.dewey', 'available'])
            return render_template('searchResults.html', rows = df)
    return render_template('search.html')

# October 28th update - Shawnie Houston
# Below will allow standard users and librarians to do a global search after a local search.
# Global search will use search data from the previous local search.
@app.route('/searchAll')
def search_all():
    srch = session['srch']
    cat = session['cat']

    with sql.connect("Library.db") as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        # if user wants to search by book
        if cat == 'book':
            # return book name, author, description, genre, library name, and dewey decimal number
            sql_query = '''SELECT b.bookID, b.bookName, b.author, b.description, b.genre, l.libraryName, b.dewey, \
                            CASE WHEN lo.bookID IS NULL THEN 1 ELSE 0 END AS available \
                            FROM Books b JOIN Libraries l ON b.libraryID = l.libraryID \
                            LEFT JOIN Loans lo ON b.bookID = lo.bookID WHERE b.bookName LIKE ?;'''
            cur.fetchall()
            cur.execute(sql_query, ('%' + srch + '%',))
        # if user wants to search by author
        elif cat == 'author':
            # return book name, author, description, genre, library name, and dewey decimal number
            sql_query = '''SELECT b.bookID, b.bookName, b.author, b.description, b.genre, l.libraryName, b.dewey, \
                            CASE WHEN lo.bookID IS NULL THEN 1 ELSE 0 END AS available \
                            FROM Books b JOIN Libraries l ON b.libraryID = l.libraryID \
                            LEFT JOIN Loans lo ON b.bookID = lo.bookID WHERE b.author LIKE ?;'''
            cur.fetchall()
            cur.execute(sql_query, ('%' + srch + '%',))
        # if user wants to search by genre
        elif cat == 'genre':
            # return book name, author, description, genre, library name, and dewey decimal number
            sql_query = '''SELECT b.bookID, b.bookName, b.author, b.description, b.genre, l.libraryName, b.dewey, \
                            CASE WHEN lo.bookID IS NULL THEN 1 ELSE 0 END AS available \
                            FROM Books b JOIN Libraries l ON b.libraryID = l.libraryID \
                            LEFT JOIN Loans lo ON b.bookID = lo.bookID WHERE b.genre LIKE ?;'''
            cur.fetchall()
            cur.execute(sql_query, ('%' + srch + '%',))
        # if user wants to search by library
        elif cat == 'library':
            # return book name, author, description, genre, library name, and dewey decimal number
            sql_query = '''SELECT b.bookID, b.bookName, b.author, b.description, b.genre, l.libraryName, b.dewey, \
                            CASE WHEN lo.bookID IS NULL THEN 1 ELSE 0 END AS available \
                            FROM Books b JOIN Libraries l ON b.libraryID = l.libraryID \
                            LEFT JOIN Loans lo ON b.bookID = lo.bookID WHERE l.libraryName LIKE ?;'''
            cur.fetchall()
            cur.execute(sql_query, ('%' + srch + '%',))
    # build data frame to send
    df = pd.DataFrame(cur.fetchall(),
                      columns=['b.bookID','b.bookName', 'b.author', 'b.description', 'b.genre', 'l.libraryName', 'b.dewey', 'available'])
    return render_template('searchResults.html', rows=df)

# October 18th merge update:
# Josh:
# Added functions to access enterNew page to add/remove materials from library

# This function looks at Libraries table and returns the list of unique library names for dropdowns
@app.route('/libraryList',methods=['POST', 'GET'])
def library_list():
    con = sql.connect("Library.db")
    con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("SELECT DISTINCT libraryName FROM Libraries")
    library_names = [row[0] for row in cur.fetchall()]
    con.close()
    return jsonify(library_names)

# Function to add new book to library inventory
@app.route('/enterNew', methods=['POST', 'GET'])
def enterNew():
    if not session.get('logged_in'):
        return render_template('login.html')
    elif session.get('admin') == 2 or session.get('admin') == 3:
        if session.get('admin') == 3:
            selected_library = request.form.get('selectedLibrary')
        else:
            selected_library = session['UserLocalLibraryName']

        if request.form.get('AddBook'):
            title = request.form['AddBookTitle']
            author = request.form['AddBookAuthor']
            pub = request.form['AddBookPublisher']
            isbn = request.form['AddBookISBN']
            desc = request.form['AddBookDescription']
            genre = request.form['AddBookGenre']
            dewey = request.form['AddBookDeweyDecimal']

            message = ""  # initialization of blank string for error message
            errors = 0  # initialization of error counter

            # if statements to catch blank inputs
            if (len(title) == 0):
                message = message + "Can not add inventory, Book title is required\n"
                errors += 1
            if (len(author) == 0):
                message = message + "Can not add inventory, Book author is required\n"
                errors += 1
            if (len(pub) == 0):
                message = message + "Can not add inventory, Book publisher is required\n"
                errors += 1
            if (len(isbn) == 0):
                message = message + "Can not add inventory, Book ISBN is required\n"
                errors += 1
            if (len(desc) == 0):
                message = message + "Can not add inventory, Book description is required\n"
                errors += 1
            if (len(genre) == 0):
                message = message + "Can not add inventory, Book genre is required\n"
                errors += 1
            if (len(dewey) == 0):
                message = message + "Can not add inventory, Book dewey decimal is required\n"
                errors += 1
            if (errors > 0):  # if error counter > 0, display all error messages generated
                message = message.split('\n')
                return render_template("result.html", msg=message)


            try:
                with sql.connect("Library.db") as con:
                    cur = con.cursor()
                    # selected library needs to be in parentheses with a comma to force it to be parsed as string
                    cur.execute("Select libraryID from Libraries where libraryName = ?", (selected_library,))
                    #cur.fetchone returns a tuple. only want to access 1st element
                    result = cur.fetchone()
                    libID = result[0]
                    cur.execute("INSERT INTO Books (libraryID,"
                                "bookName,"
                                "author,"
                                "publisher,"
                                "isbn13,"
                                "description,"
                                "genre,"
                                "dewey) "
                                "VALUES (?,?,?,?,?,?,?,?)", (libID, title, author, pub, isbn, desc, genre, dewey))

                    con.commit()
                    message = message + "Inventory successfully added\n"

            except Exception as e:
                con.rollback()
                print(f"Error: {e}")
                message = message + "error in insert operation\n" + f"Error: {e}"

            finally:
                message = message.split('\n')
                return render_template("result.html", msg=message)
                con.close()


        elif request.form.get('RemoveBook'):
            message = ""  # initialization of blank string for error message
            try:
                title = request.form['RemoveBookTitle']
                author = request.form['RemoveBookAuthor']
                pub = request.form['RemoveBookPublisher']
                isbn = request.form['RemoveBookISBN']
                with sql.connect("Library.db") as con:
                    con.row_factory = sql.Row
                    cur = con.cursor()

                    # tries to match book to entry in table

                    sql_select_query = """select * from Books \
                                        join Libraries on Books.libraryID = libraries.libraryID \
                                        where bookName = ? and author = ? and publisher = ? and isbn13 = ? and libraryName = ?"""
                    cur.execute(sql_select_query, (title,author,pub,isbn,selected_library))
                    row = cur.fetchone()
                    if (row != None):  # this is true if a record is found
                        sql_delete_query = """Delete from Books where bookID in (  \
                                                               select Books.bookID from Books \
                                                               join Libraries on Books.libraryID = libraries.libraryID \
                                                               where bookName = ? and author = ? and publisher = ? and isbn13 = ? and libraryName = ?)"""
                        cur.execute(sql_delete_query, (title, author, pub, isbn, selected_library))
                        con.commit()
                        message = message + "Inventory successfully deleted\n"
                    else:
                        flash("Book not found in inventory, cannot delete")

            except Exception as e:
                con.rollback()
                print(f"Error: {e}")
                message = message + "error in delete operation\n" + f"Error: {e}"

            finally:
                message = message.split('\n')
                return render_template("result.html", msg=message)
                con.close()

        return render_template('enterNew.html', UserInventoryLibrary=selected_library)
    else:
        abort(404)

# October 28th 2024 update
# Josh Knorr
# Added code to handle case where user's home library gets deleted. Route to html page to choose new library

@app.route('/changeLibrary', methods=['POST', 'GET'])
def changeLibrary():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        # this needs to be here or page won't render when accessed directly from home link
        if request.method == 'POST':
            message = ''
            selected_library = request.form.get('selectedLibrary')
            try:
                with sql.connect("Library.db") as con:
                    cur = con.cursor()
                    # selected library needs to be in parentheses with a comma to force it to be parsed as string
                    cur.execute("Select libraryID from Libraries where libraryName = ?", (selected_library,))
                    # cur.fetchone returns a tuple. only want to access 1st element
                    result = cur.fetchone()
                    libID = result[0]
                    cur.execute("UPDATE LibUsers SET libraryID = ? WHERE userLogon = ? "
                                , (libID, session.get('username')))
                    con.commit()

                    message = message + "Library successfully updated.\n"


            except Exception as e:
                con.rollback()
                print(f"Error: {e}")
                message = message + "error in update operation\n" + f"Error: {e}"

            finally:
                message = message.split('\n')
                #need to set both integer user local library and string user local library name
                #or else issues with displaying correct books for level 2 users when showing
                #books checked out by user's local library
                session['UserLocalLibrary'] = libID
                session['UserLocalLibraryName'] = selected_library
                return render_template("result.html", msg=message)
                con.close()

        return render_template("changeLibrary.html", google_maps_key=GOOGLE_MAPS_API_KEY)


# November 3rd update - Josh Knorr
# code to handle check out button - when clicked from search results, will check out book and add to loans table
@app.route('/checkOut', methods=['POST', 'GET'])
def check_out():
    if not session.get('logged_in'):   # if user not logged in and tries to access this page, redirect to login
        return render_template('login.html')
    else:
        book_id = request.json.get('bookID')
        user_logon = request.json.get('userLogon')  # Assuming you have a way to get the user's logon

        if not book_id or not user_logon:
            return jsonify({'error': 'Missing bookID or userLogon'}), 400

        try:
            con = sql.connect("Library.db")
            con.row_factory = sql.Row
            cur = con.cursor()
            cur.execute("INSERT INTO Loans (bookID,userLogon) Values (?,?)",(book_id,user_logon))
            con.commit()
            return jsonify({'success': True, 'message': 'Book checked out successfully'}), 200

        except Exception as e:
            print(e)
            return jsonify({'error': 'Failed to check out the book'}), 500

# November 11th - Shawnie Houston
# Handles check in button
# When button is clicked, book will be removed from Loans table
@app.route('/checkIn', methods=['POST', 'GET'])
def check_in():
    if not session.get('logged_in'):   # if user not logged in and tries to access this page, redirect to login
        return render_template('login.html')
    else:
        book_id = request.json.get('bookID')
        print(book_id)

        if not book_id:
            return jsonify({'error': 'Missing bookID'}), 400

        try:
            con = sql.connect("Library.db")
            print("1")
            con.row_factory = sql.Row
            print("2")
            cur = con.cursor()
            print("3")
            cur.execute("DELETE FROM Loans WHERE bookID = ?",(book_id,))
            print("4")
            con.commit()
            print("5")
            return jsonify({'success': True, 'message': 'Book checked in successfully'}), 200

        except Exception as e:
            print(e)
            return jsonify({'error': 'Failed to check in the book'}), 500

@app.route("/logout")
# if user clicks logout link, resets variables
def logout():
    session['logged_in'] = False  # reset logged_in to false
    session['admin'] = 1
    session['name'] = ""
    return home()


if __name__ == '__main__':
    app.secret_key = os.urandom(12)  # generate random number
    # need secret key to generate session variable
    app.run(debug=True)