from flashcard.core import db
from sqlalchemy.sql import func
from sqlalchemy.orm import backref

class Deck(db.Model):
    __tablename__ = "deck"
    deck_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    deck_title = db.Column(db.String(120), nullable=False)
    created_on = db.Column(db.DateTime, server_default=func.now())

    cards = db.relationship("Card", cascade="all,delete", backref="deck")

class DeckTag(db.Model):
    __tablename__ = "deck_tag"

    deck_id = db.Column(db.Integer, db.ForeignKey("deck.deck_id"), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey("tag.tag_id"), primary_key=True)

    card = db.relationship("Deck", backref=backref("tags", cascade="all,delete"))
    tag = db.relationship("Tag", backref=backref("deck_tags", cascade="all,delete"))
