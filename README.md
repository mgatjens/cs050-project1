# Project 1

Web Programming with Python and JavaScript

1. init.bat: is a script that contains the environment variables to run the application over Windows 10.
2. Notes.txt: contains some notes about the database access and other access.
3. Tables.txt: contains the description of the database tables created for the project.
4. import.py: the python program to import the datas into "books" table.

templates:
1. layout.html: header and footer for inheritance to all the HTML pages.
2. index.html: login html
3. register.html: the html page to register a new user.
4. books.html: the html page to search for books. For search I used only one field for the three filters.
5. bookdetail.html: the html page to show the selected book's detail, the reviews and the option to register a new review.

Application.py
1.
I used the variables:
    session['iduser']
    session["username"]
    session["name"]
to register the user access to the application and the database transactions.

2.
The first part contains all the methods used for query and transactions to the database.
The second part contains all the logical methods

3. the las method is the API.
to invoque the API you need to use:
http://127.0.0.1:5000/api/0451216725
where the last number is one isbn book number

4. Link youtube demo
https://youtu.be/DaginiiNqQ4