import csv
import os

from flask import Flask, render_template, request
from models import *

# from sqlalchemy import create_engine
# from sqlalchemy.orm import scoped_session, sessionmaker

# engine = create_engine(os.getenv("DATABASE_URL"))
# db = scoped_session(sessionmaker(bind=engine))

# Tell Flask what SQLAlchemy databas to use.
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Link the Flask app with the database (no Flask app is actually being run yet).
db.init_app(app)

def main():
    # Create Tables in Database
    db.create_all()
    # Add Entries in Books table from books.csv file
    f=open("books.csv")
    reader = csv.reader(f)
    for isbn, title, author, year in reader:
        # db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", {"isbn":isbn, "title":title, "author":author, "year":year})
        book = Books(isbn=isbn, title=title, author=author, year=year)
        db.session.add(book)
        print(f"Added \"{title}\" written by {author} in year {year}")
    db.session.commit()

if __name__ == "__main__":
    with app.app_context():
        main()
