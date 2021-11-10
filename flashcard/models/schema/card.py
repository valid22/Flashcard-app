from flashcard.core import db
from sqlalchemy.sql import func
from sqlalchemy.orm import backref

class Card(db.Model):
    __tablename__ = "card"

    card_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    card_deck = db.Column(db.Integer, db.ForeignKey("deck.deck_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)

    card_front = db.Column(db.String, nullable=False)
    card_back = db.Column(db.String, nullable=False)

    created_on = db.Column(db.DateTime, server_default=func.now())

class CardTag(db.Model):
    __tablename__ = "card_tag"

    card_id = db.Column(db.Integer, db.ForeignKey("card.card_id"), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey("tag.tag_id"), primary_key=True)

    card = db.relationship("Card", backref=backref("tags", cascade="all,delete"))
    tag = db.relationship("Tag", backref=backref("card_tags", cascade="all,delete"))
