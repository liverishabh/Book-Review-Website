import os

from flask import Flask, session, render_template, request, flash, redirect
from flask_session import Session
from models import *
from passlib.hash import pbkdf2_sha256
from sqlalchemy import and_
import requests
# import jinja2
# from sqlalchemy import create_engine
# from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
# engine = create_engine(os.getenv("DATABASE_URL"))
# db = scoped_session(sessionmaker(bind=engine))
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Link the Flask app with the database (no Flask app is actually being run yet).
db.init_app(app)


@app.route("/")
def login():
    # session.clear()
    # session["username"] = None
    return render_template("login.html")

@app.route("/search", methods=["GET", "POST"])
def search():
    # Get form information
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Make sure Username exists in database
        # user = db.execute("SELECT * FROM users WHERE username=:username", {"username":username}).fetchall()
        user = User.query.filter_by(username=username).first()
        if user is None:
            return render_template("error.html", message="username", login=True)
        else:
            if(pbkdf2_sha256.verify(password,user.pass_hash)):
                session["username"] = user.username
                flash('You were successfully logged in!')
                return render_template("search.html")
            else:
                return render_template("error.html", message="password", login=True) # login is True because I want to login.

    else:
        try:
            if session["username"] is not None:
                return render_template("search.html")
        except KeyError:
            return "<h1> Method Not Allowed </h1> <p> The method is not allowed for the requested URL.</p>"


@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/register_result", methods=["POST"])
def register_result():
    # Get form information
    firstname = request.form.get("firstname")
    lastname = request.form.get("lastname")
    username = request.form.get("username")
    password = request.form.get("password")

    # Check if username already exists
    if(User.query.filter_by(username=username).first() is not None):
        if(User.query.filter_by(username=username).first().username == username):
            return render_template("error.html", message=f"Username {username} is already taken.", login=False)

    # Generate pass hash
    pass_hash = pbkdf2_sha256.hash(password)

    # Add User
    user = User(firstname=firstname, lastname=lastname, username=username, pass_hash=pass_hash)
    db.session.add(user)
    db.session.commit()

    return render_template("success.html", user=user)

@app.route("/search_result", methods=["POST"])
def search_result():
    # Get form information
    searchBy = request.form.get("options")
    searchKey = request.form.get("search")

    if(searchBy=="title"):
        books = Books.query.filter(Books.title.ilike(f"%{searchKey}%")).all()
    elif(searchBy=="author"):
        books = Books.query.filter(Books.author.ilike(f"%{searchKey}%")).all()
    elif(searchBy=="year"):
        books = Books.query.filter(Books.year.like(f"%{searchKey}%")).all()
    elif(searchBy=="isbn"):
        books = Books.query.filter(Books.isbn.like(f"%{searchKey}%")).all()

    if books is None:
        return render_template("error.html")
    else:
        return render_template("results.html", books=books)

@app.route("/books/<int:book_id>")
def book(book_id):
    try:
        if session["username"] is not None:
            book = Books.query.get(book_id)

            GoodReads_Key = "PvLrxsvj6CwLBJBmtWzQ4w"
            res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": GoodReads_Key , "isbns": book.isbn})
            review = res.json()['books'][0]

            reviews = book.reviews
            user_id = [review.user_id for review in reviews]
            username = [User.query.filter_by(id=user_id).first().username for user_id in user_id]

            # env = jinja2.Environment()
            # env.globals.update(zip=zip)
            app.jinja_env.filters['zip'] = zip

            return render_template("book.html", book=book, review=review, reviews=reviews, username=username)

    except KeyError:
        return "<h1> Method Not Allowed </h1> <p> The method is not allowed for the requested URL.</p>"


@app.route("/books/<int:book_id>/add_review", methods=["POST"])
def add_review(book_id):
    book = Books.query.get(book_id)
    book_id = book.id

    user = User.query.filter_by(username=session["username"]).first()
    user_id = user.id

    # if you query for all(), then review will not be None, even if review list is empty (nothing is returned from databse).
    # But, if you query for first(), then it will be None, if nothing is returned from databse.
    review = Reviews.query.filter(and_(Reviews.book_id == book_id, Reviews.user_id == user_id)).first()

    if review is not None:
        # flash('You have already added a review')
        return render_template("review.html", book_id=book_id, review=False)
        # return redirect("/books/"+str(book_id))
        # return "Failed"

    rating = int(request.form.get("rating"))
    comment = request.form.get("comment")

    review = Reviews(rating=rating, comment=comment, user_id=user_id, book_id=book_id)

    db.session.add(review)
    db.session.commit()

    # flash("Book Review added")
    # return redirect("/books/"+str(book_id))
    return render_template("review.html", book_id=book_id, review=True)

@app.route("/logout")
def logout():
    try:
        if session["username"] is not None:
            session.clear()
            flash("You were successfully logged out!")
            return render_template("logout.html")
    except KeyError:
        return "<h1> Method Not Allowed </h1> <p> The method is not allowed for the requested URL.</p>"

# @app.route("/api/<string:isbn>")
# def api_call(isbn):
#     book = Books.query.filter_by(isbn=isbn).first()
#
#     if book is None:
#         return jsonify({"Error": "Invalid book ISBN"}), 422
