import os
import datetime

from flask import Flask, render_template, session, request, jsonify
from flask_session import Session
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import scoped_session, sessionmaker

import requests

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

#configure database access
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#define session variables
def login_usr( iduser, username, name):
    session['iduser']  = iduser
    session['username'] = username
    session['name'] = name

def logout_usr():
    session['iduser']  = 0
    session["username"] = ''
    session["name"] = ''

def LoginValid():
    if not session["iduser"]:
        return False
    elif session["iduser"] != 0:
        return True
    else:
        return False

#################################################################################################################################
### Database methods
#################################################################################################################################

def book_rating(idbook):
    #calculate the rating and count reviews for a book
    reviews = db.execute("SELECT  count(idreview) as countreviews, COALESCE(sum(rating)/count(idreview),0) as rating FROM reviews WHERE idbook = :idbook", 
                                {"idbook": idbook}).fetchone()        
    return reviews

def user_exist(username):
    #search for a specific username
    user = db.execute("SELECT iduser, username, name, password FROM users WHERE username = :username", 
                       {"username": username}).fetchone()
    
    return user

def password_valid(username, password):
    #search for username and password
    user = db.execute("SELECT iduser, username, name, password FROM users WHERE username = :username AND password = :password", 
                       {"username": username, "password": password}).fetchone()
    
    return user

def user_insert(username, name, password):
    #insert a new user 
    iduser = db.execute("INSERT INTO users (iduser, username, name, password) VALUES (DEFAULT, :username, :name, :password) RETURNING iduser",
                        {"username": username, "name": name, "password": password}).fetchone()[0]
    db.commit()
    return iduser

def Books_Search(filter_search):
    #search for books by title or isbn or author
    books = db.execute("SELECT idbook, isbn, title, author, year FROM books WHERE (title like :filter_search OR isbn like :filter_search OR author like :filter_search)",
                        {"filter_search": '%{}%'.format(filter_search)}).fetchall()
    return books

def Books_Search_count(filter_search):
    books = db.execute("SELECT count(idbook) as countbook FROM books WHERE (title like :filter_search OR isbn like :filter_search OR author like :filter_search)",
                        {"filter_search": '%{}%'.format(filter_search)}).fetchone()
    return (books.countbook > 0)

def  Books_x_id(idbook):
    #search for a book by id
    book = db.execute("SELECT idbook, isbn, title, author, year FROM books WHERE idbook = :idbook",
                        {"idbook": idbook}).fetchone()
    return book

def  Books_x_isbn(isbn):
    #search for a book by isbn
    book = db.execute("SELECT idbook, isbn, title, author, year FROM books WHERE iisbn = :isbn",
                        {"isbn": isbn}).fetchone()
    return book

def Book_count_isbn(isbn):
    book = db.execute("SELECT COUNT(isbn) as count from books WHERE isbn = :isbn",
                        {"isbn": isbn}).fetchone()
    
    return book.count

def Reviews(idbook):
    #select reviews data for a book
    reviews = db.execute("SELECT idreview, idbook, datereview, users.iduser as iduser, users.username as username, users.name as name, rating, opinion FROM reviews INNER JOIN users ON users.iduser = reviews.iduser WHERE idbook = :idbook",
                            {"idbook": idbook}).fetchall()
    return reviews

def User_did_review(idbook, iduser):
    review = db.execute("SELECT COUNT(idreview) FROM reviews WHERE idbook = :idbook AND iduser =  :iduser",
                        {"idbook": idbook, "iduser": iduser}).fetchone()
    if review is None:
        return False

    return (review[0] > 0)

def Review_insert(idbook, datereview, iduser, rating, opinion):
    #insert a new review
    db.execute("INSERT INTO reviews (idreview, idbook, datereview, iduser, rating, opinion) VALUES (DEFAULT, :idbook, :datereview, :iduser, :rating, :opinion)",
                {"idbook": idbook, "datereview": datereview, "iduser": iduser, "rating": rating, "opinion": opinion})
    db.commit()

#################################################################################################################################

@app.route("/")
def index():
    logout_usr()
    return render_template("index.html")

@app.route("/logout")
def logout():
    logout_usr()
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    if request.form['btnlogin'] == 'btnregister': 
        return render_template("register.html")
    else:
        try:
            usr = request.form.get("username")
            pswd = request.form.get("pswd")

            if (not usr or not pswd):
                return render_template("error.html", message="Username or password invalid.")
            
            usrexist = password_valid(username = usr, password =pswd)
            if not usrexist :
                logout_usr()
                return render_template("error.html", message="User or password invalid. Please try again")
            else:
                login_usr(iduser=usrexist.iduser, username=usrexist.username, name=usrexist.name)
                return render_template("books.html", name=session["name"], existbooks=False)
        except ValueError:
            return render_template("error.html", message="Username or password invalid.")

        #validate if username and pws exist
        return render_template("error.html", message="To register the user, first You need to include all the fields.")

@app.route("/register", methods=["POST"])
def register_user():
    if request.form['btnregister'] == 'btnregister': 
        #validate all fields are required
        try:
            usr = request.form.get("username")
            name = request.form.get("name")
            pswd = request.form.get("pswd")
        except ValueError:
            return render_template("error.html", message="To register the user, first You need to include all the fields.")
        
        if (not usr or not name or not pswd):
            return render_template("error.html", message="To register the user, first You need to include all the fields.")

        #validate if username exist
        usrexist = user_exist(username = usr)
        if usrexist is None:
            #if username not exist, create user
            iduser = user_insert(username=usr, name=name,  password=pswd)
            login_usr(iduser=iduser, username=usr, name=name)
            return render_template("books.html", name=session["name"], existbooks=False)
        else:
            return render_template("error.html", message="Username is not available.  Please try with other username.")
    else: #accion is cancel 
        logout_usr()
        return render_template("index.html")

@app.route("/books")
def books():
    if not LoginValid():
        logout_usr()
        return render_template("index.html")
    else:
        return render_template("books.html", name=session["name"], existbooks=False)

@app.route("/books", methods=["POST"])
def search_book():
    if not LoginValid():
        logout_usr()
        return render_template("index.html")

    try:
        filter_search = request.form.get("filter_search")
        if filter_search:
            books = Books_Search(filter_search=filter_search)
            existbooks = Books_Search_count(filter_search=filter_search)

            return render_template("books.html", name=session["name"], existbooks=existbooks, books=books)
        else:
            return render_template("books.html", name=session["name"], existbooks=False)
    except ValueError:
        return render_template("error.html", message="Error ocurred.")
    
@app.route("/bookreviews/<int:idbook>")
def bookreviews(idbook):
    if not LoginValid():
        logout_usr()
        return render_template("index.html")
    
    try:
        #get book selected data
        book = Books_x_id(idbook=idbook)
        if book  is None:
            return render_template("error.html", message="No Books.")

        #get booksreview                
        bookreviews = Reviews(idbook=idbook)
        bookrating =  book_rating(idbook=idbook)
        if bookrating is None:
            countreviews = 0
            rating = 0
        else:
            countreviews = bookrating.countreviews
            rating = bookrating.rating

        key = "VistzmuAVfB3oVsjhCvlzA"

        response = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": book.isbn})
        if response.status_code == 200:
            json_response = response.json()
            data = json_response["books"][0]
            goodreads_rating = data["average_rating"]
            goodreads_numberratings = data["work_ratings_count"]
        else:
            goodreads_rating = 0
            goodreads_numberratings = 0

        return render_template("bookdetail.html", name=session["name"], book=book, bookreviews=bookreviews, rating=rating, countreviews=countreviews, goodreads_rating=goodreads_rating, goodreads_numberratings=goodreads_numberratings)
    except ValueError:
        return render_template("error.html", message="Error ocurred.")

@app.route("/register_review/<int:idbook>", methods=["POST"])
def register_review(idbook):
    if request.form['btnregisterreview'] == 'btnregisterreview':  
        try:

            idbookreview  = idbook
            datereview = datetime.datetime.now()
            iduser = session['iduser']
            rating = request.form.get("my_rating")
            opinion = request.form.get("review_text")

            if (not rating or not opinion):
                return render_template("error.html", message="To register the review, first You need to include all the fields.")

            #check if the user already did  a review for the book 
            if User_did_review(idbook=idbook, iduser=iduser):
                return render_template("error.html", message="You already register one review for this book.")

            #insert new review
            Review_insert(idbook=idbook, datereview=datereview, iduser=iduser, rating=rating, opinion=opinion)

            return bookreviews(idbook=idbookreview)
        except ValueError:
            return render_template("error.html", message="To register the review, first You need to include all the fields.")

##############################################################
### API for GET request
@app.route("/api/<string:isbn>")
def isbn_api(isbn):

    #check if the isbn exist, if don't return error
    if Book_count_isbn(isbn=isbn) == 0:
        return jsonify({"error": "Invalid isbn " + isbn}), 404

    #get the isbn's book data
    book = db.execute("SELECT idbook, title, author, year, isbn  FROM books WHERE isbn = :isbn",
                            {"isbn": isbn}).fetchone()
    idbook = book.idbook   

    #get rating and count of review's book     
    reviews = book_rating(idbook)        

    return jsonify({
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "isbn": book.isbn,
        "review_count": reviews.countreviews,
        "average_score": reviews.rating
        })