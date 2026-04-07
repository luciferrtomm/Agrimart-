from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100))

    password = db.Column(db.String(200))

    address = db.Column(db.String(200))

    contact = db.Column(db.String(20))

    role = db.Column(db.String(20))


class Product(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100))

    price = db.Column(db.Float)

    description = db.Column(db.Text)

    category = db.Column(db.String(100))

    image = db.Column(db.String(200))   # NEW COLUMN

    farmer_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class Cart(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer)

    product_id = db.Column(db.Integer)

    quantity = db.Column(db.Integer)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    total_price = db.Column(db.Float)
    status = db.Column(db.String(50), default="Pending")

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer)
    product_id = db.Column(db.Integer)
    quantity = db.Column(db.Integer)        


    