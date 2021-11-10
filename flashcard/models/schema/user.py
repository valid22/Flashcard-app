from flashcard.core import db
from sqlalchemy.sql import func
from sqlalchemy.orm import backref

class User(db.Model):
    __tablename__ = "user"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False) # sha256 hash

    name = db.Column(db.String(120), nullable=False)
    registered_on = db.Column(db.DateTime, server_default=func.now())

class UserDeck(db.Model):
    __tablename__ = "user_deck"

    card_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), primary_key=True)
    deck_id = db.Column(db.Integer, db.ForeignKey("deck.deck_id"), primary_key=True)


    user = db.relationship("User", backref=backref("decks", cascade="all,delete"))
    deck = db.relationship("Deck", backref=backref("user_decks", cascade="all,delete"))
