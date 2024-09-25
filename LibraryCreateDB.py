"""
Name: Josh Knorr
Date: 10/25/2023
Assignment: Module 8: Send Authenticated Message.
Due Date:10/22/2023
About this project: The purpose of this project is to add log in and role based access control to previous assignment.
In this version, certain security levels have access to certain functions, while others do not. The program reads in
the users security access level based on inputted user name, matching it to sql table.
Assumptions: Assumes HospitalUsers table is created before users run Update script. Assumes UserTestResults table is
created before users run script. Assume users run HMAC and Test Result server.
All work below was performed by Josh Knorr, with code inspired by Dr Works CrapsDB example
Some code recycled from previous assignments of this course by Josh Knorr. Some code provided by Dr Works
"""
import sqlite3
import Encryption

key = b'\x89\xcc\x01y\xfd\xbd\xcd=Gv\x99m\xa5\x9f?f\x02\x86\xc9#\xea\xf7\xc3e\xd6\xa0\t\x06D\xad<\x84'
iv = b'w\xdb^K%\\\xf5,`\xc7\xbb\xabs\x1f\x06\x16'

cipher = Encryption.AESCipher(key,iv)

#create new DB, or if already created connect to it

conn = sqlite3.connect('Library.db')

#create cursor to execute queries

cur = conn.cursor()

#drop table from database if exists - try catch block


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


# create table in database
cur.execute('''CREATE TABLE Books(
BookId INTEGER PRIMARY KEY NOT NULL,
BookName TEXT NOT NULL,
ISBN13 INTEGER NOT NULL,
Author TEXT NOT NULL,
Publisher TEXT NOT NULL,
CheckedOut BOOLEAN NOT NULL,
LibraryLocation TEXT NOT NULL,
DeweyDecimal TEXT NOT NULL);
''')

cur.execute('''CREATE TABLE LibUsers(
UserId INTEGER PRIMARY KEY NOT NULL,
UserName TEXT NOT NULL,
UserPhNum TEXT NOT NULL,
UserAddress TEXT NOT NULL,
UserLocalLibrary TEXT NOT NULL,
SecurityLevel INTEGER NOT NULL,
LoginPassword TEXT NOT NULL);
''')

cur.execute('''CREATE TABLE Loans(
UserId INTEGER NOT NULL,
BookId INTEGER NOT NULL,
CheckedOut DATE NOT NULL,
ReturnBy DATE NOT NULL,
PRIMARY KEY (UserId,BookId));
''')


# Create list of users
'''
Users = [(cipher.encrypt('JKnorr'),cipher.encrypt('123-675-7645'),cipher.encrypt('123 Street lane'),('FSU PC Library'),1,cipher.encrypt('test123')),
         (cipher.encrypt('IQuintero'),cipher.encrypt('895-345-6523'),cipher.encrypt('123 Street lane'),('FSU PC Library'),2,cipher.encrypt('test123')),
         (cipher.encrypt('PGuardia'),cipher.encrypt('428-197-3967'),cipher.encrypt('123 Street lane'),('FSU PC Library'),3,cipher.encrypt('test123')),
         (cipher.encrypt('SHouston'),cipher.encrypt('239-567-3498'),cipher.encrypt('123 Street lane'),('FSU PC Library'),2,cipher.encrypt('test123'))]


# executemany command to add entire list of users to table all at once

cur.executemany('Insert into LibUsers(UserName,'
                'UserPhNum,'
                'UserAddress,'
                'UserLocalLibrary,'
                'SecurityLevel,'
                'LoginPassword) Values(?,?,?,?,?,?)', Users)
            
'''
# test code from chatgpt
# 1. Insert entries into the Books table
books_data = [
    (1, 'The Catcher in the Rye', 9780316769488, 'J.D. Salinger', 'Little, Brown and Company', True, 'Central Library', '813.52'),
    (2, 'To Kill a Mockingbird', 9780061120084, 'Harper Lee', 'J.B. Lippincott & Co.', True, 'Central Library', '813.54'),
    (3, '1984', 9780451524935, 'George Orwell', 'Secker & Warburg', False, 'Westside Library', '823.912'),
    (4, 'Moby Dick', 9781503280786, 'Herman Melville', 'Harper & Brothers', True, 'Central Library', '813.3'),
    (5, 'Pride and Prejudice', 9781503290563, 'Jane Austen', 'T. Egerton', False, 'Eastside Library', '823.7'),
    (6, 'The Great Gatsby', 9780743273565, 'F. Scott Fitzgerald', 'Charles Scribner\'s Sons', True, 'Central Library', '813.52'),
    (7, 'War and Peace', 9780199232765, 'Leo Tolstoy', 'The Russian Messenger', False, 'Westside Library', '891.73'),
    (8, 'The Hobbit', 9780547928227, 'J.R.R. Tolkien', 'George Allen & Unwin', True, 'Eastside Library', '823.912'),
    (9, 'Crime and Punishment', 9780140449136, 'Fyodor Dostoevsky', 'The Russian Messenger', False, 'Central Library', '891.733'),
    (10, 'The Odyssey', 9780140268867, 'Homer', 'Penguin Classics', True, 'Eastside Library', '883.01')
]

cur.executemany('''
    INSERT INTO Books (BookId, BookName, ISBN13, Author, Publisher, CheckedOut, LibraryLocation, DeweyDecimal)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
''', books_data)

# 2. Insert entries into the LibUsers table
users_data = [
    (1, cipher.encrypt('Alice Johnson'), cipher.encrypt('555-1234'), cipher.encrypt('123 Maple St'), 'Central Library', 1, cipher.encrypt('password1')),
    (2, cipher.encrypt('BobSmith'), cipher.encrypt('555-5678'), cipher.encrypt('456 Oak St'), 'Westside Library', 1, cipher.encrypt('password2')),
    (3, cipher.encrypt('CharlieDavis'), cipher.encrypt('555-9101'), cipher.encrypt('789 Pine St'), 'Central Library', 2, cipher.encrypt('password3')),
    (4, cipher.encrypt('DianaRoss'), cipher.encrypt('555-1122'), cipher.encrypt('321 Elm St'), 'Eastside Library', 1, cipher.encrypt('password4')),
    (5, cipher.encrypt('EvanLee'), cipher.encrypt('555-3344'), cipher.encrypt('654 Birch St'), 'Central Library', 3, cipher.encrypt('password5')),
    (6, cipher.encrypt('FionaGreen'), cipher.encrypt('555-5566'), cipher.encrypt('987 Cedar St'), 'Eastside Library', 1, cipher.encrypt('password6')),
    (7, cipher.encrypt('GeorgeKing'),cipher.encrypt('555-7788'), cipher.encrypt('111 Spruce St'), 'Westside Library', 1, cipher.encrypt('password7')),
    (8, cipher.encrypt('HelenClark'), cipher.encrypt('555-9900'), cipher.encrypt('222 Redwood St'), 'Central Library', 1, cipher.encrypt('password8')),
    (9, cipher.encrypt('IanTurner'), cipher.encrypt('555-0011'), cipher.encrypt('333 Willow St'), 'Eastside Library', 2, cipher.encrypt('password9')),
    (10, cipher.encrypt('JanePorter'), cipher.encrypt('555-2233'), cipher.encrypt('444 Cypress St'), 'Westside Library', 3, cipher.encrypt('password10'))
]

cur.executemany('''
    INSERT INTO LibUsers (UserId, UserName, UserPhNum, UserAddress, UserLocalLibrary, SecurityLevel, LoginPassword)
    VALUES (?, ?, ?, ?, ?, ?, ?)
''', users_data)

# 3. Insert entries into the Loans table
loans_data = [
    (1, 1, '2024-09-01', '2024-09-15'),
    (3, 2, '2024-09-03', '2024-09-17'),
    (8, 4, '2024-09-05', '2024-09-19'),
    (6, 8, '2024-09-04', '2024-09-18'),
    (9, 10, '2024-09-02', '2024-09-16'),
    (5, 6, '2024-09-06', '2024-09-20')
]

cur.executemany('''
    INSERT INTO Loans (UserId, BookId, CheckedOut, ReturnBy)
    VALUES (?, ?, ?, ?)
''', loans_data)


# save changes
conn.commit()
print('tables created')

# iterate over the rows and print results from select statement
for row in cur.execute('SELECT * FROM LibUsers;'):
    #print(row[0],cipher.decrypt(row[1]),cipher.decrypt(row[2]),cipher.decrypt(row[3]),row[4],row[5],cipher.decrypt(row[6]))
    print(row)


for row in cur.execute('SELECT * FROM Books;'):
    print(row)

for row in cur.execute('SELECT * FROM Loans;'):
    print(row)

# close database connection
conn.close()
print('Connection closed.')