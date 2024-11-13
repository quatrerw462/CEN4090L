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
- Added option for standard users and librarians to search all libraries after an initial local search
- Added functionality for standard users to see their borrowed books
- Added functionality for librarians and admins to view loaned books
- Above three written by Shawnie


<h3>Update (October 28th pt 2):</h3>

- Added functionality to check if user had their library deleted. If so, forces selection of new library
- Added functionality for all users to change their libraries
- Written by Josh

<h3>Update (October 31st):</h3>

- Added default values to checkedOut and returnBy attributes in Loans table
- Written by Josh

  
<h3>Update (November 3rd):</h3>

- Added check out functionality, merged with search
- Changed how loans works, now displays books checked out by logged in user vs user's home library
- Written by Josh

<h3>Update (November 8th):</h3>

- Created base.html template to be used as parent for all the other .html templates (makes it a lot more concise for styling and global elements)
- Added graphical elements (LitManager logo as a vector for lossless scalability, books texture to be overlayed over the background)
- Created style.css to be the center for the UI's theme customization. It is divided into sections and includes text styling, background styling, button styling, etc.
- Borrowed a 'particles' java-script library created by Vincent Garreau a few years ago (https://github.com/VincentGarreau/particles.js); it will only be used for styling. It has been customized to fit with our project's color scheme (FSU colors).
- Written by Isaias

<h3>Update (November 12th):</h3>

- Updated the style.css to include more customization for the templates.
- Updated 6 .html templates to match style of the scheme so far and to extend from base.html.
- Written by Isaias
