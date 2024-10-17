# October 16th merge update:
# Majority of this file replaced by Shawnie's version.
# Table schemas have been updated to their latest version according to the Project Tracking spreadsheet.
# Initial version written by Joshua.
# Second version written by Shawnie.
# Merging into project and additional changes by Pablo.

import sqlite3
from datetime import datetime, timedelta
import Encryption

key = b'\x89\xcc\x01y\xfd\xbd\xcd=Gv\x99m\xa5\x9f?f\x02\x86\xc9#\xea\xf7\xc3e\xd6\xa0\t\x06D\xad<\x84'
iv = b'w\xdb^K%\\\xf5,`\xc7\xbb\xabs\x1f\x06\x16'

cipher = Encryption.AESCipher(key,iv)

# Connect to SQLite database
conn = sqlite3.connect('Library.db')
cur = conn.cursor()

try:
    conn.execute('''Drop table Books''')
    #save changes
    conn.commit()
    print('Books table dropped')
except:
    print('Books table did not exist')

try:
    conn.execute('''Drop table LibUsers''')
    #save changes
    conn.commit()
    print('LibUsers table dropped')
except:
    print('LibUsers table did not exist')

try:
    conn.execute('''Drop table Loans''')
    #save changes
    conn.commit()
    print('Loans table dropped')
except:
    print('Loans table did not exist')

try:
    conn.execute('''Drop table UpgradeReqs''')
    #save changes
    conn.commit()
    print('UpgradeReqs table dropped')
except:
    print('UpgradeReqs table did not exist')

try:
    conn.execute('''Drop table Libraries''')
    #save changes
    conn.commit()
    print('Libraries table dropped')
except:
    print('Libraries table did not exist')


# Create tables
cur.execute('''
CREATE TABLE IF NOT EXISTS Books (
    bookID INTEGER PRIMARY KEY AUTOINCREMENT,
    libraryID INTEGER,
    bookName TEXT COLLATE NOCASE NOT NULL,
    author TEXT COLLATE NOCASE,
    publisher TEXT,
    isbn13 TEXT,
    description TEXT,
    genre TEXT COLLATE NOCASE,
    dewey TEXT,
    FOREIGN KEY (libraryID) REFERENCES Libraries(libraryID)
)
''')

cur.execute('''
CREATE TABLE IF NOT EXISTS LibUsers (
    userLogon TEXT PRIMARY KEY NOT NULL,
    libraryID INTEGER,
    firstName TEXT NOT NULL,
    lastName TEXT NOT NULL,
    phoneNum TEXT NOT NULL,
    userAddress TEXT NOT NULL,
    userCity TEXT NOT NULL,
    userState TEXT NOT NULL,
    userZip TEXT NOT NULL,
    securityLevel INTEGER NOT NULL,
    password TEXT NOT NULL,
    FOREIGN KEY (libraryID) REFERENCES Libraries(libraryID)
)
''')

cur.execute('''
CREATE TABLE IF NOT EXISTS Loans (
    bookID INTEGER NOT NULL,
    userLogon TEXT NOT NULL,
    checkedOut DATETIME NOT NULL,
    returnBy DATETIME NOT NULL,
    PRIMARY KEY (bookID, userLogon),
    FOREIGN KEY (bookID) REFERENCES Books(bookID),
    FOREIGN KEY (userLogon) REFERENCES LibUsers(userLogon)
)
''')

# UpgradeReqs table for handling security level upgrade requests data
# Created by Pablo
cur.execute('''
CREATE TABLE IF NOT EXISTS UpgradeReqs(
    RequestId INTEGER PRIMARY KEY NOT NULL,
    UserLogon TEXT UNIQUE NOT NULL,
    UserName TEXT NOT NULL,
    CurrentLevel INTEGER NOT NULL,
    DesiredLevel INTEGER NOT NULL,
    DateOfRequest DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    Reason TEXT NOT NULL,
    InvExperience TEXT NOT NULL,
    NetExperience TEXT NOT NULL,
    Tasks TEXT NOT NULL
)
''')

# Libraries table created by Shawnie
cur.execute('''
CREATE TABLE IF NOT EXISTS Libraries (
    libraryID INTEGER PRIMARY KEY AUTOINCREMENT,
    libraryName TEXT COLLATE NOCASE NOT NULL,
    libraryAddress TEXT NOT NULL,
    libraryCity TEXT NOT NULL,
    libraryState TEXT NOT NULL,
    libraryZip TEXT NOT NULL
)
''')



# Insert sample data into Books
books = [
    (1, 'The Great Gatsby', 'F. Scott Fitzgerald', 'Scribner', '9780743273565', 'A novel set in the 1920s.', 'Fiction', '813.52'),
    (1, '1984', 'George Orwell', 'Harcourt', '9780451524935', 'Dystopian novel about totalitarianism.', 'Fiction', '823.912'),
    (2, 'To Kill a Mockingbird', 'Harper Lee', 'J.B. Lippincott & Co.', '9780061120084', 'A novel about racial injustice.', 'Fiction', '813.54'),
    (2, 'The Catcher in the Rye', 'J.D. Salinger', 'Little, Brown and Company', '9780316769488', 'A story about teenage alienation.', 'Fiction', '813.54'),
    (3, 'Moby Dick', 'Herman Melville', 'Richard Bentley', '9781503280786', 'A novel about obsession and revenge.', 'Fiction', '813.3'),
    (3, 'Pride and Prejudice', 'Jane Austen', 'T. Egerton', '9781503290563', 'A romantic novel that critiques the British landed gentry.', 'Fiction', '823.7'),
    (4, 'The Old Man and the Sea', 'Ernest Hemingway', 'Charles Scribner\'s Sons', '9780684830490', 'A story of an aging fisherman\'s struggle.', 'Fiction', '813.54'),
    (4, 'The Road', 'Cormac McCarthy', 'Alfred A. Knopf', '9780307387899', 'A post-apocalyptic novel.', 'Fiction', '813.54'),
]

cur.executemany('''
INSERT INTO Books (libraryID, bookName, author, publisher, isbn13, description, genre, dewey) 
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
''', books)

users = [
    ('jdoe', 1, 'John', 'Doe', '555-1234', '789 Pine St', 'Florida City', 'FL', '33034', 1, 'password123'),
    ('asmith', 2, 'Alice', 'Smith', '555-5678', '321 Oak St', 'Homestead', 'FL', '33030', 2, 'mypassword'),
    ('bwhite', 1, 'Bob', 'White', '555-8765', '654 Maple St', 'Florida City', 'FL', '33034', 1, 'securepass'),
    ('cjohnson', 3, 'Charlie', 'Johnson', '555-4321', '111 Elm St', 'Key Largo', 'FL', '33037', 2, 'charliepass'),
    ('dlee', 4, 'Diana', 'Lee', '555-6789', '222 Cedar St', 'Everglades City', 'FL', '34139', 1, 'dianapass'),
    ('ewilliams', 1, 'Ethan', 'Williams', '555-9876', '333 Birch St', 'Florida City', 'FL', '33034', 3, 'ethanpass'),
    ('fgarcia', 2, 'Fiona', 'Garcia', '555-3456', '444 Willow St', 'Homestead', 'FL', '33030', 2, 'fionapass'),
    ('hclark', 3, 'Henry', 'Clark', '555-8765', '555 Palm St', 'Key Largo', 'FL', '33037', 1, 'henrypass'),
]

# Encrypt the user data
encrypted_users = [
    (
        userLogon,
        libraryID,
        cipher.encrypt(firstName),
        cipher.encrypt(lastName),
        cipher.encrypt(phoneNum),
        cipher.encrypt(userAddress),
        cipher.encrypt(userCity),
        cipher.encrypt(userState),
        cipher.encrypt(userZip),
        securityLevel,
        cipher.encrypt(password)
    )
    for userLogon, libraryID, firstName, lastName, phoneNum, userAddress, userCity, userState, userZip, securityLevel, password in users
]

cur.executemany('''
INSERT INTO LibUsers (userLogon, libraryID, firstName, lastName, phoneNum, userAddress, userCity, userState, userZip, securityLevel, password) 
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', encrypted_users)

# Insert sample data into Loans
loans = [
    (1, 'jdoe', datetime.now(), datetime.now() + timedelta(days=21)),
    (2, 'asmith', datetime.now(), datetime.now() + timedelta(days=21)),
    (3, 'bwhite', datetime.now(), datetime.now() + timedelta(days=21)),
    (4, 'cjohnson', datetime.now(), datetime.now() + timedelta(days=21)),
    (5, 'dlee', datetime.now(), datetime.now() + timedelta(days=21)),
    (6, 'ewilliams', datetime.now(), datetime.now() + timedelta(days=21)),
    (7, 'fgarcia', datetime.now(), datetime.now() + timedelta(days=21)),
    (8, 'hclark', datetime.now(), datetime.now() + timedelta(days=21)),
]

cur.executemany('''
INSERT INTO Loans (bookID, userLogon, checkedOut, returnBy) 
VALUES (?, ?, ?, ?)
''', loans)

# Insert sample data into Libraries
libraries = [
    ('Florida Bay County Library', '123 Main St', 'Florida City', 'FL', '33034'),
    ('Homestead Public Library', '456 Library Ave', 'Homestead', 'FL', '33030'),
    ('Key Largo Library', '789 Ocean Dr', 'Key Largo', 'FL', '33037'),
    ('Everglades City Library', '101 River Rd', 'Everglades City', 'FL', '34139'),
]

cur.executemany('''
INSERT INTO Libraries (libraryName, libraryAddress, libraryCity, libraryState, libraryZip) 
VALUES (?, ?, ?, ?, ?)
''', libraries)


# save changes
conn.commit()
print('tables created')

# iterate over the rows and print results from select statement
for row in cur.execute('SELECT * FROM LibUsers;'):
    print(row)

for row in cur.execute('SELECT * FROM Books;'):
    print(row)

for row in cur.execute('SELECT * FROM Libraries;'):
    print(row)

for row in cur.execute('SELECT * FROM Loans;'):
    print(row)

# close database connection
conn.close()
print('Connection closed.')