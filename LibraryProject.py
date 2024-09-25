
from flask import Flask, render_template, request, session, flash, jsonify, abort

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

# definition of home page, return home.html
@app.route('/')
def home():
    if not session.get('logged_in'):   # if user not logged in and tries to access this page, redirect to login
        return render_template('login.html')
    else:
        return render_template('home.html', name=session['name'], UserLocalLibrary=session['UserLocalLibrary'])

# definition of create account, return createAccount.html

@app.route('/createAccount')
def create_account():
    return render_template('createAccount.html')


# definition of list borrowed materials, return loans.html
@app.route('/loans')
def loans():
    if not session.get('logged_in'):   # if user not logged in and tries to access this page, redirect to login
        return render_template('login.html')
    else:
        return render_template('loans.html', name=session['name'])


# definition of check out materials, return checkOut.html
@app.route('/checkOut')
def check_out():
    if not session.get('logged_in'):   # if user not logged in and tries to access this page, redirect to login
        return render_template('loans.html')
    else:
        return render_template('checkOut.html', name=session['name'])



# definition of showUser, return show.html
@app.route('/showUser')
def show_user():
    if not session.get('logged_in'):   # if user not logged in and tries to access this page, redirect to login
        return render_template('login.html')
    else:  # open conenction to sql table to display info about logged in user
        con = sql.connect("Library.db")
        con.row_factory = sql.Row

        cur = con.cursor()
        sql_select_query = """select UserName,UserPhNum,UserAddress,UserLocalLibrary,SecurityLevel,LoginPassword from LibUsers where UserName = ? """
        cur.execute(sql_select_query, [cipher.encrypt(session['name'])])
        df = pd.DataFrame(cur.fetchall(),
                          columns=['UserName', 'UserPhNum', 'UserAddress', 'UserLocalLibrary', 'SecurityLevel',
                                   'LoginPassword']);

        # UserName
        df.iat[0, 0] = cipher.decrypt(df.iat[0, 0])
        # UserPhNum
        df.iat[0, 1] = cipher.decrypt(df.iat[0, 1])
        # UserAddress
        df.iat[0, 2] = cipher.decrypt(df.iat[0, 2])
        # LoginPassword
        df.iat[0, 5] = cipher.decrypt(df.iat[0, 5])

        return render_template("show.html", row=df)


# definition of add rec, when user.html is called, this function is called
@app.route('/addrec', methods=['POST', 'GET'])
def addrec():

    if request.method == 'POST':

        nm = request.form['Name']
        ph = request.form['PhoneNumber']
        ad = request.form['Address']
        ll = request.form['LocalLibrary']
        sec = request.form['SecurityLevel']
        pwd = request.form['Password']

        nm = str(nm).strip()  # removes whitespace
        ph = str(ph).strip()  # removes whitespace
        ad = str(ad).strip()  # removes whitespace
        ll = str(ll).strip()  # removes whitespace
        pwd = str(pwd).strip()  # removes whitespace

        message = ""  # initialization of blank string for error message
        errors = 0  # initialization of error counter

# try except else block for input validation of security level parameter
        try:
            value = int(sec)
        except ValueError:
            message = message + "debug test, SecurityRoleLevel must be an integer between 1 and 3\n"
            errors += 1
        else:
            if int(sec) < 1 or int(sec) > 3:
                message = message + "debug test, SecurityRoleLevel must be an integer between 1 and 3\n"
                errors += 1
# if statements to catch blank inputs
        if (len(nm) == 0):
            message = message + "Can not create account, Name is required\n"
            errors += 1
        if (len(ph)==0):
            message = message + "Can not create account, Phone Number is required\n"
            errors += 1

        if (len(ad)==0):
            message = message + "Can not create account, Address is required\n"
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

                    nm = cipher.encrypt(nm)
                    ph = cipher.encrypt(ph)
                    ad = cipher.encrypt(ad)
                    pwd = cipher.encrypt(pwd)

                    cur.execute("INSERT INTO LibUsers (UserName,"
                                "UserPhNum,"
                                "UserAddress,"
                                "UserLocalLibrary,"
                                "SecurityLevel,"
                                "LoginPassword) "
                                "VALUES (?,?,?,?,?,?)",(nm, ph, ad, ll, sec, pwd))

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
@app.route('/list')
def list():
    if not session.get('logged_in'):   # if user not logged in and tries to access this page, redirect to login
        return render_template('login.html')
    elif session.get('admin') == 2:  # checks if user security level is 2
        con = sql.connect("Library.db")
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("SELECT b.BookName, u.UserName, b.LibraryLocation, l.CheckedOut, l.ReturnBy \
                FROM Books b JOIN Loans l ON b.BookId = l.BookId \
                JOIN LibUsers u ON l.UserId = u.UserId WHERE b.CheckedOut = TRUE \
                AND u.UserLocalLibrary = ?;", [session['UserLocalLibrary']])

        df = pd.DataFrame(cur.fetchall(), columns=['b.BookName','u.UserName', 'b.LibraryLocation', 'l.CheckedOut', 'l.ReturnBy'])
        return render_template("list.html", rows = df)

    elif session.get('admin') == 3:  # checks if user security level is 3
        con = sql.connect("Library.db")
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("SELECT b.BookName, u.UserName, b.LibraryLocation, l.CheckedOut, l.ReturnBy \
                FROM Books b JOIN Loans l ON b.BookId = l.BookId \
                JOIN LibUsers u ON l.UserId = u.UserId WHERE b.CheckedOut = TRUE;")
        df = pd.DataFrame(cur.fetchall(), columns=['b.BookName','u.UserName', 'b.LibraryLocation', 'l.CheckedOut', 'l.ReturnBy'])
        return render_template("list.html", rows = df)
    else:
        abort(404)  # if user does not have high enough security level, return 404 error


@app.route('/login', methods=['POST'])
def do_admin_login():

   try:
      nm = request.form['username']  # reads in inputted username and password from login.html
      pwd = request.form['password']
      name = nm
      with sql.connect("Library.db") as con:
         con.row_factory = sql.Row
         cur = con.cursor()

         nm = cipher.encrypt(nm)  # encrypts name and pwd to match to encrypted forms in table
         pwd = cipher.encrypt(pwd)
# tries to match username and password to entry in table
         sql_select_query = """select * from LibUsers where UserName = ? and LoginPassword = ?"""
         cur.execute(sql_select_query, (nm,pwd))

         row = cur.fetchone();
         if (row != None):  # this is true if a record is found
            session['logged_in'] = True  # if log in successful, set logged_in to true
            session['name'] = name  # sets session['name'] to name entered as user name in log in field
            # below if statements to set users security level, which is held in the session['admin'] variable
            # this comes from sql table
            session['UserLocalLibrary'] = row['UserLocalLibrary']
            session['UserId'] = int(row['UserId'])
            if (int(row['SecurityLevel'])==3):
               session['admin'] = 3
            elif(int(row['SecurityLevel'])==2):
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

#Code for enter test results page - only admin level 3 can access and enter new test results
@app.route('/enterTestResult')
def new_TestResult():
   if not session.get('logged_in'):
      return render_template('login.html')
   elif session.get('admin') == 2 or session.get('admin') == 3:
     return render_template('newTestResult.html')
   else:
       abort(404)
"""
# Holdover code from old assignment
#code to enter new test results - validates input and encrypts
@app.route('/addTestResults', methods=['POST', 'GET'])
def addTestResult():
   if not session.get('logged_in'):
      return render_template('login.html')
   elif session.get('admin') == 2 or session.get('admin') == 3:
      if request.method == 'POST':
         try:
            error = False
            testNm = request.form['TestName']
            testResult = request.form['TestResult']
            UserId = request.form['UserId']
            testNm = str(testNm).lstrip()
            testResult = str(testResult).lstrip()

            msg = "\n"
            if (len(testNm) == 0):
               error = True
               msg += "You can not enter in an empty test name \n"

            if (len(testResult) == 0):
               error = True
               msg += "You can not enter in an empty test Result \n"

            try:
               if (int(UserId) <= 0):
                  error = True
                  msg += "The User Id must be a whole number greater than 0. \n"
            except ValueError:
               error = True
               msg += "The User Id must be a whole number greater than 0. \n"
            # below code executes if all input valid
            if (not (error)):
               sep = "^%$"  # separator
               msg = UserId+sep+testNm+sep+testResult  #concatenates inputted fields with separator to send to server
               msg = cipher.encrypt(msg)
            # code to access server
               HOST, PORT = "localhost", 9999
               sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
               # Connect to server and send data
               sock.connect((HOST, PORT))

               sock.sendall(msg)
               sock.close()

               msg = "Help message sent!"


         finally:
            msg = msg.split('\n')
            return render_template("result.html", msg=msg)
   else:
       abort(404)

# displays test results - accesses test results table and decrpyts
@app.route('/testResults')
def testResults():
   if not session.get('logged_in'):
      return render_template('login.html')
   else:
      con = sql.connect("HospitalUser.db")
      con.row_factory = sql.Row

      cur = con.cursor()
      cur.execute("select TestName, TestResult from UserTestResults where UserId = ?",[session['UserId']])
      df = pd.DataFrame(cur.fetchall(),
                        columns=['TestName', 'TestResult']);
      df['TestName'] = df['TestName'].apply(lambda x: cipher.decrypt(x))
      df['TestResult'] = df['TestResult'].apply(lambda x: cipher.decrypt(x))
      print(df)
      return render_template("TestResults.html", rows=df)
"""
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
