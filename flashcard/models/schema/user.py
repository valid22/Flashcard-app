from flashcard.core import db
from sqlalchemy.sql import func
from sqlalchemy.orm import backref

class User(db.Model):
    __tablename__ = "user"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False) # sha256 hash

    registered_on = db.Column(db.DateTime, server_default=func.now())
    decks = db.relationship("Deck", cascade="all,delete", backref="user")
