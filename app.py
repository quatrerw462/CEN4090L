from flask import Flask, render_template, request, session, jsonify, abort, redirect, url_for, flash
from utils import fetch_all, execute_query, decrypt_columns
import os

app = Flask(__name__)

# -------------------------
# Utility Functions
# -------------------------

def require_login():
    """Redirect to login page if the user is not logged in."""
    if not session.get('logged_in'):
        return render_template('login.html')

def require_admin_level(level):
    """Check if the user's admin level is sufficient."""
    if session.get('admin', 1) < level:
        flash("Insufficient privileges to access this page.")
        return redirect(url_for('home'))

# -------------------------
# Routes
# -------------------------

@app.route('/')
def home():
    """Render the home page or redirect based on session status."""
    if not session.get('logged_in'):
        return render_template('login.html')
    if session.get('UserLocalLibraryName') == -1:
        return render_template('changeLibrary.html')
    return render_template('home.html', name=session['name'], UserLocalLibrary=session['UserLocalLibraryName'])

@app.route('/createAccount')
def create_account():
    """Render the create account page."""
    return render_template('createAccount.html')

@app.route('/loans')
def loans():
    """Display user's currently borrowed materials."""
    if require_login():
        return require_login()

    query = """
    SELECT b.bookName, lo.checkedOut, lo.returnBy, lib.libraryName 
    FROM Loans lo
    JOIN Books b ON b.bookID = lo.bookID
    JOIN Libraries lib ON lib.libraryID = b.libraryID
    WHERE lo.userLogon = ?;
    """
    user_logon = session['username']
    loans_df = fetch_all(query, (user_logon,))
    return render_template("loans.html", rows=loans_df)

@app.route('/showUser')
def show_user():
    """Display the logged-in user's details."""
    if require_login():
        return require_login()

    query = """
    SELECT firstName, lastName, phoneNum, userAddress, Libraries.libraryName, securityLevel, password 
    FROM LibUsers
    JOIN Libraries ON LibUsers.libraryID = Libraries.libraryID
    WHERE userLogon = ?;
    """
    user_data = fetch_all(query, (session['username'],))
    decrypted_data = decrypt_columns(user_data, ['firstName', 'lastName', 'phoneNum', 'userAddress', 'password'])
    request_exists_query = "SELECT UserLogon FROM UpgradeReqs WHERE UserLogon = ?"
    request_exists = fetch_all(request_exists_query, (session['username'],)).empty is False
    return render_template("show.html", row=decrypted_data, requestExists=request_exists)

@app.route('/addrec', methods=['POST'])
def addrec():
    """Add a new user account to the database."""
    if request.method == 'POST':
        fields = ['UserName', 'FirstName', 'LastName', 'PhoneNumber', 'Address', 'City', 'State', 'Zip', 'selectedLibrary', 'Password']
        data = {field: request.form.get(field, "").strip() for field in fields}

        if any(len(value) == 0 for value in data.values()):
            errors = [f"{field} is required" for field, value in data.items() if len(value) == 0]
            return render_template("result.html", msg=errors)

        library_query = "SELECT libraryID FROM Libraries WHERE libraryName = ?"
        library_result = fetch_all(library_query, (data['selectedLibrary'],))
        if library_result.empty:
            return render_template("result.html", msg=["Local library does not exist."])

        data['libraryID'] = library_result.iloc[0]['libraryID']
        encrypted_data = {key: cipher.encrypt(value) if key != 'libraryID' else value for key, value in data.items()}

        insert_query = """
        INSERT INTO LibUsers (userLogon, libraryID, firstName, lastName, phoneNum, userAddress, userCity, userState, userZip, securityLevel, password)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        try:
            execute_query(insert_query, tuple(encrypted_data.values()))
            return render_template("result.html", msg=["Account successfully created."])
        except Exception as e:
            return render_template("result.html", msg=[f"Error creating account: {e}"])

@app.route('/list')
def list_books():
    """Display a list of all books in the library based on the user's security level."""
    if require_login():
        return require_login()

    user_level = session.get('admin', 1)
    library_id = session.get('UserLocalLibrary')

    if user_level < 2:
        abort(404)  # Insufficient privileges

    base_query = """
    SELECT b.bookName, u.firstName, u.lastName, lib.libraryName, lo.checkedOut, lo.returnBy, b.bookID
    FROM Loans lo
    JOIN LibUsers u ON u.userLogon = lo.userLogon
    JOIN Books b ON b.bookID = lo.bookID
    JOIN Libraries lib ON lib.libraryID = b.libraryID
    """

    if user_level == 2:  # Local librarian
        query = base_query + "WHERE b.libraryID = ?;"
        books_df = fetch_all(query, (library_id,))
    else:  # Admin
        query = base_query + ";"
        books_df = fetch_all(query)

    decrypted_books = decrypt_columns(books_df, ['firstName', 'lastName'])
    return render_template("list.html", rows=decrypted_books)

@app.route('/request')
def request_upgrade():
    """Render the page for users to request a security level upgrade."""
    if require_login():
        return require_login()
    return render_template('requestUpgrade.html')

@app.route('/requestSent', methods=['POST'])
def submit_upgrade_request():
    """Handle the submission of a security level upgrade request."""
    if require_login():
        return require_login()

    user_data = {
        'UserLogon': session.get('username'),
        'UserName': cipher.encrypt(session.get('name')),
        'CurrentLevel': session.get('admin'),
        'DesiredLevel': request.form.get('levelChoice', 3),
        'Reason': request.form.get('Reason'),
        'InvExperience': cipher.encrypt(request.form.get('InvExperience', "")),
        'NetExperience': cipher.encrypt(request.form.get('NetExperience', "")),
        'Tasks': request.form.get('Tasks', ""),
    }

    insert_query = """
    INSERT INTO UpgradeReqs (UserLogon, UserName, CurrentLevel, DesiredLevel, Reason, InvExperience, NetExperience, Tasks)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """
    try:
        execute_query(insert_query, tuple(user_data.values()))
        flash("Upgrade request submitted successfully!")
        return redirect(url_for('show_user'))
    except Exception as e:
        flash(f"Failed to submit request: {e}")
        return redirect(url_for('request_upgrade'))

@app.route('/requestList')
def list_requests():
    """Display all user upgrade requests for level 3 administrators."""
    if require_login() or require_admin_level(3):
        return require_login()

    query = "SELECT * FROM UpgradeReqs;"
    requests_df = fetch_all(query)
    decrypted_requests = decrypt_columns(requests_df, ['UserName', 'InvExperience', 'NetExperience'])
    return render_template('showRequests.html', rows=decrypted_requests)

@app.route('/upgrade')
def upgrade_user():
    """Handle the acceptance or rejection of a user upgrade request."""
    if require_login() or require_admin_level(3):
        return require_login()

    user_id = request.args.get('id')
    request_id = request.args.get('reqID', type=int)
    new_level = request.args.get('level', type=int)
    accept = request.args.get('accept', default="false").lower() == "true"

    if not user_id or request_id is None or new_level is None:
        flash("Invalid request parameters.")
        return redirect(url_for('list_requests'))

    try:
        with connect_db() as con:
            cur = con.cursor()
            if accept:
                cur.execute("UPDATE LibUsers SET securityLevel = ? WHERE userLogon = ?", (new_level, user_id))
            cur.execute("DELETE FROM UpgradeReqs WHERE RequestId = ?", (request_id,))
            con.commit()
        flash("Request processed successfully.")
    except Exception as e:
        flash(f"Failed to process request: {e}")
    return redirect(url_for('list_requests'))

@app.route('/searchResults', methods=['POST'])
def search_results():
    """Search for books based on the user's criteria."""
    if require_login():
        return require_login()

    search_term = request.form.get('libsearch', "")
    category = request.form.get('category', "")
    user_level = session.get('admin', 1)
    user_library = session.get('UserLocalLibrary')

    category_mapping = {
        'book': "b.bookName LIKE ?",
        'author': "b.author LIKE ?",
        'genre': "b.genre LIKE ?",
        'library': "l.libraryName LIKE ?"
    }

    if category not in category_mapping:
        flash("Invalid search category.")
        return redirect(url_for('search'))

    base_query = """
    SELECT b.bookID, b.bookName, b.author, b.description, b.genre, l.libraryName, b.dewey,
           CASE WHEN lo.bookID IS NULL THEN 1 ELSE 0 END AS available
    FROM Books b
    JOIN Libraries l ON b.libraryID = l.libraryID
    LEFT JOIN Loans lo ON b.bookID = lo.bookID
    """

    if user_level < 3:  # Local search for non-admins
        base_query += "WHERE l.libraryID = ? AND " + category_mapping[category]
        params = (user_library, f"%{search_term}%")
    else:  # Global search for admins
        base_query += "WHERE " + category_mapping[category]
        params = (f"%{search_term}%",)

    results_df = fetch_all(base_query, params)
    return render_template("searchResults.html", rows=results_df)

@app.route('/checkOut', methods=['POST'])
def check_out():
    """Handle the checkout of a book."""
    if require_login():
        return require_login()

    book_id = request.json.get('bookID')
    user_logon = session.get('username')

    if not book_id:
        return jsonify({'error': 'Missing bookID'}), 400

    query = "INSERT INTO Loans (bookID, userLogon) VALUES (?, ?);"
    try:
        execute_query(query, (book_id, user_logon))
        return jsonify({'success': True, 'message': 'Book checked out successfully'}), 200
    except Exception as e:
        return jsonify({'error': f"Failed to check out the book: {e}"}), 500

@app.route('/checkIn', methods=['POST'])
def check_in():
    """Handle the check-in of a book."""
    if require_login():
        return require_login()

    book_id = request.json.get('bookID')

    if not book_id:
        return jsonify({'error': 'Missing bookID'}), 400

    query = "DELETE FROM Loans WHERE bookID = ?;"
    try:
        execute_query(query, (book_id,))
        return jsonify({'success': True, 'message': 'Book checked in successfully'}), 200
    except Exception as e:
        return jsonify({'error': f"Failed to check in the book: {e}"}), 500

@app.route('/addLibForm')
def add_library_form():
    """Render the form to add a new library."""
    if require_login() or require_admin_level(3):
        return require_login()
    return render_template('addLibrary.html')


@app.route('/addLib', methods=['POST'])
def add_library():
    """Add a new library to the database."""
    if require_login() or require_admin_level(3):
        return require_login()

    library_data = {
        'libraryName': request.form.get('libName', "").strip(),
        'libraryAddress': request.form.get('libAddress', "").strip(),
        'libraryCity': request.form.get('libCity', "").strip(),
        'libraryState': request.form.get('libState', "").strip(),
        'libraryZip': request.form.get('libZip', "").strip(),
    }

    if any(len(value) == 0 for value in library_data.values()):
        errors = [f"{field} is required" for field, value in library_data.items() if len(value) == 0]
        return render_template("result.html", msg=errors)

    insert_query = """
    INSERT INTO Libraries (libraryName, libraryAddress, libraryCity, libraryState, libraryZip)
    VALUES (?, ?, ?, ?, ?);
    """
    try:
        execute_query(insert_query, tuple(library_data.values()))
        flash("Library added successfully!")
    except Exception as e:
        flash(f"Failed to add library: {e}")
    return redirect(url_for('showLibs'))


@app.route('/showLibs')
def show_libraries():
    """Display all libraries."""
    if require_login() or require_admin_level(3):
        return require_login()

    query = "SELECT * FROM Libraries;"
    libraries_df = fetch_all(query)
    return render_template("listLibraries.html", rows=libraries_df)


@app.route('/deleteLib')
def delete_library():
    """Delete a library by its ID."""
    if require_login() or require_admin_level(3):
        return require_login()

    library_id = request.args.get('libID', type=int)
    if library_id is None:
        flash("Invalid library ID.")
        return redirect(url_for('show_libraries'))

    delete_query = "DELETE FROM Libraries WHERE libraryID = ?;"
    try:
        execute_query(delete_query, (library_id,))
        flash("Library deleted successfully.")
    except Exception as e:
        flash(f"Failed to delete library: {e}")
    return redirect(url_for('show_libraries'))


@app.route('/changeLibrary', methods=['POST', 'GET'])
def change_library():
    """Allow a user to update their local library."""
    if require_login():
        return require_login()

    if request.method == 'POST':
        selected_library = request.form.get('selectedLibrary', "").strip()
        if not selected_library:
            flash("No library selected.")
            return render_template('changeLibrary.html')

        try:
            library_query = "SELECT libraryID FROM Libraries WHERE libraryName = ?;"
            library_result = fetch_all(library_query, (selected_library,))
            if library_result.empty:
                flash("Selected library does not exist.")
                return render_template('changeLibrary.html')

            library_id = library_result.iloc[0]['libraryID']
            update_query = "UPDATE LibUsers SET libraryID = ? WHERE userLogon = ?;"
            execute_query(update_query, (library_id, session['username']))
            session['UserLocalLibrary'] = library_id
            session['UserLocalLibraryName'] = selected_library
            flash("Library updated successfully.")
        except Exception as e:
            flash(f"Failed to update library: {e}")
    return render_template('changeLibrary.html')


@app.route('/enterNew', methods=['POST', 'GET'])
def manage_inventory():
    """Add or remove books from the library inventory."""
    if require_login() or require_admin_level(2):
        return require_login()

    selected_library = request.form.get('selectedLibrary', session.get('UserLocalLibraryName'))

    if request.method == 'POST':
        if 'AddBook' in request.form:
            book_data = {
                'bookName': request.form.get('AddBookTitle', "").strip(),
                'author': request.form.get('AddBookAuthor', "").strip(),
                'publisher': request.form.get('AddBookPublisher', "").strip(),
                'isbn': request.form.get('AddBookISBN', "").strip(),
                'description': request.form.get('AddBookDescription', "").strip(),
                'genre': request.form.get('AddBookGenre', "").strip(),
                'dewey': request.form.get('AddBookDeweyDecimal', "").strip(),
            }

            if any(len(value) == 0 for value in book_data.values()):
                errors = [f"{field} is required" for field, value in book_data.items() if len(value) == 0]
                return render_template("result.html", msg=errors)

            try:
                library_query = "SELECT libraryID FROM Libraries WHERE libraryName = ?;"
                library_result = fetch_all(library_query, (selected_library,))
                if library_result.empty:
                    flash("Selected library does not exist.")
                    return render_template("enterNew.html")

                library_id = library_result.iloc[0]['libraryID']
                book_data['libraryID'] = library_id
                insert_query = """
                INSERT INTO Books (libraryID, bookName, author, publisher, isbn13, description, genre, dewey)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """
                execute_query(insert_query, tuple(book_data.values()))
                flash("Book added successfully.")
            except Exception as e:
                flash(f"Failed to add book: {e}")

        elif 'RemoveBook' in request.form:
            book_data = {
                'bookName': request.form.get('RemoveBookTitle', "").strip(),
                'author': request.form.get('RemoveBookAuthor', "").strip(),
                'publisher': request.form.get('RemoveBookPublisher', "").strip(),
                'isbn': request.form.get('RemoveBookISBN', "").strip(),
            }

            if any(len(value) == 0 for value in book_data.values()):
                errors = [f"{field} is required" for field, value in book_data.items() if len(value) == 0]
                return render_template("result.html", msg=errors)

            try:
                delete_query = """
                DELETE FROM Books 
                WHERE bookName = ? AND author = ? AND publisher = ? AND isbn13 = ? 
                AND libraryID = (SELECT libraryID FROM Libraries WHERE libraryName = ?);
                """
                execute_query(delete_query, (*book_data.values(), selected_library))
                flash("Book removed successfully.")
            except Exception as e:
                flash(f"Failed to remove book: {e}")

    return render_template("enterNew.html", UserInventoryLibrary=selected_library)


@app.route('/logout')
def logout():
    """Log out the current user by resetting session variables."""
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
