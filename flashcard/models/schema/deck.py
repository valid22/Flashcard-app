from flashcard.core import db
from sqlalchemy.sql import func
from sqlalchemy.orm import backref


deck_tag_association = db.Table('deck_tag', db.Model.metadata,
    db.Column('deck_id', db.Integer, db.ForeignKey('deck.deck_id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.tag_id'))
)
class Deck(db.Model):
    __tablename__ = "deck"
    deck_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"))

    deck_title = db.Column(db.String(120), nullable=False)
    deck_img = db.Column(db.String(6692), nullable=False, default="default")
    created_on = db.Column(db.DateTime, server_default=func.now())

    cards = db.relationship("Card", cascade="all,delete", backref="deck")
    tags = db.relationship("Tag", secondary=deck_tag_association, backref="decks")
    reviews = db.relationship("Review", cascade="all,delete", backref="deck")

