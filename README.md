<h3>Running on Python 3.12</h3>

<h3>Update (October 17th):</h3>

- Removed users' ability to choose their security level when creating a new account.

- Users' security level is now 1 by default, and they can only get a higher level by filling out a security upgrade request form.
  
- Requests can only be seen, accepted, and rejected by level 3 users.
  
- Fixed issue in the listing of loans, where users who checked out their books would have their names encrypted on display.
  
- Updated SQL table schemas, and changed code to reflect these changes.
  
- Users can now specify extra fields when creating an account, such as their first and last name, as well as their city, state, and zip code.
  
- Added search function for database. Not implemented into the website for easy access, but a preliminary version is up and running. Type '/search' after the URL to test it out.
  
- All code in this update written by Pablo and Shawnie. Merged together and pushed into repository by Pablo.


<h3>Update (October 21st):</h3>

- Added functionality to add and remove books to database
- Level 3 users can choose which library, level 2 users can only add/remove from the library associated with their account


<h3>Update (October 28th):</h3>

- Added triggers to LibraryCreateDB.py; these are used as a fallback in case the ON DELETE statements don't work (they didn't work for me while I was testing them.

- Added comments to the add/remove library functions I wrote some time ago.

- Code written by Pablo.
