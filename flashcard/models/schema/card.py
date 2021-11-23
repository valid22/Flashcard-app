from flashcard.core import db
from sqlalchemy.sql import func
from sqlalchemy.orm import backref

class Card(db.Model):
    __tablename__ = "card"

    card_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    deck_id = db.Column(db.Integer, db.ForeignKey("deck.deck_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)

    card_front = db.Column(db.String, nullable=False)
    card_back = db.Column(db.String, nullable=False)

    created_on = db.Column(db.DateTime, server_default=func.now(), nullable=False)
    last_reviewed = db.Column(db.DateTime, server_default=func.now(), nullable=False)
    #next_review = db.Column(db.DateTime, server_default=func.now(), nullable=False)
    
    # status = db.Column(db.Integer, nullable=False, default=0)
    # steps_index = db.Column(db.Integer, nullable=False, default=0)
    # ease_factor = db.Column(db.Integer, nullable=False, default=250)
    # interval = db.Column(db.Integer)
    
    reviews = db.relationship("Review", cascade="all,delete", backref="card")
