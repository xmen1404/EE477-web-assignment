# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from flask import Flask
from flask_sqlalchemy import SQLAlchemy


builtin_list = list


db = SQLAlchemy()


def init_app(app):
    # Disable track modifications, as it unnecessarily uses memory.
    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)
    db.init_app(app)


def from_sql(row):
    """Translates a SQLAlchemy model instance into a dictionary"""
    data = row.__dict__.copy()
    data['id'] = row.id
    data.pop('_sa_instance_state')
    return data

def process_book_item(row): 
    data = from_sql(row)
    query = Review.query.filter(Review.bookId == data['id']).with_entities(Review.rating).all()
    if len(query) == 0: 
        data['rating'] = 0
    else: 
        data['rating'] = query[0].rating
    return data
    

# [START model]
class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    author = db.Column(db.String(255))
    publishedDate = db.Column(db.String(255))
    imageUrl = db.Column(db.String(255))
    description = db.Column(db.String(4096))
    createdBy = db.Column(db.String(255))
    createdById = db.Column(db.String(255))

    def __repr__(self):
        return "<Book(title='%s', author=%s)" % (self.title, self.author)
# [END model]

# [START model]
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    userName = db.Column(db.String(255))

    def __init__(self, id, userName): 
        self.id = id
        self.userName = userName

    def __repr__(self):
        return "<User(id='%d', name=%s)" % (self.id, self.userName)
# [END model]

# [START model]
class Review(db.Model):
    __tablename__ = 'reviews'

    userId = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    bookId = db.Column(db.Integer, db.ForeignKey('books.id', ondelete='CASCADE'), primary_key=True)
    rating = db.Column(db.Integer)
    comment = db.Column(db.String(255))

    def __repr__(self):
        return "<Review(rating='%d', name=%s)" % (self.rating, self.comment)
# [END model]


# [START list]
def list(limit=10, cursor=None):
    cursor = int(cursor) if cursor else 0
    query = (Book.query
             .order_by(Book.title)
             .limit(limit)
             .offset(cursor))
    books = builtin_list(map(process_book_item, query.all()))
    next_page = cursor + limit if len(books) == limit else None
    return (books, next_page)
# [END list]


# [START read]
def read(id):
    result = from_sql(Book.query.get(id))
    review = Review.query.filter(Review.bookId == id).all()
    
    if len(review) == 0: 
        result['rating'] = 0
        result['reviewer'] = None
        result['comment'] = None 
    else: 
        reviewer = User.query.filter(User.id == review[0].userId).all()
        result['rating'] = review[0].rating
        result['reviewer'] = reviewer[0].userName
        result['comment'] = review[0].comment 
    
    if not result:
        return None
    return result
# [END read]

# [START reviewWrite]
def addReview(data):
    review = Review.query.filter(Review.bookId == data['bookId']).all()
    if len(review) > 0: 
        for k, v in data.items():
            setattr(review[0], k, v)
        db.session.commit()
        return
    newReview = Review(**data)
    db.session.add(newReview)
    db.session.commit()
# [END reviewWrite]


# [START create]
def create(data):
    book = Book(**data)
    book.createdById = 1
    book.createdBy = "root"
    db.session.add(book)
    db.session.commit()
    return from_sql(book)
# [END create]


# [START update]
def update(data, id):
    book = Book.query.get(id)
    for k, v in data.items():
        setattr(book, k, v)
    db.session.commit()
    return from_sql(book)
# [END update]


def delete(id):
    Book.query.filter_by(id=id).delete()
    db.session.commit()


def _create_database():
    """
    If this script is run directly, create all the tables necessary to run the
    application.
    """
    app = Flask(__name__)
    app.config.from_pyfile('../config.py')
    init_app(app)
    with app.app_context():
        db.create_all()
        rootUser = User(1, "root")
        db.session.add(rootUser)
        db.session.commit()

    print("All tables created")


if __name__ == '__main__':
    _create_database()
