from flashcard.core import db
from sqlalchemy.sql import func
from sqlalchemy.orm import backref


card_tag_association = db.Table('card_tag', db.Model.metadata,
    db.Column('card_id', db.Integer, db.ForeignKey('card.card_id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.tag_id'))
)

class Card(db.Model):
    __tablename__ = "card"

    card_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    deck_id = db.Column(db.Integer, db.ForeignKey("deck.deck_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)

    card_front = db.Column(db.String, nullable=False)
    card_back = db.Column(db.String, nullable=False)

    created_on = db.Column(db.DateTime, server_default=func.now())
    last_reviewed = db.Column(db.DateTime, server_default=func.now())
    
    tags = db.relationship("Tag", secondary=card_tag_association, backref="cards")
    reviews = db.relationship("Review", cascade="all,delete", backref="card")
