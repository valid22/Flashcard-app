from flashcard.core import db
from sqlalchemy.sql import func
from sqlalchemy.orm import backref

class Review(db.Model):
    __tablename__ = "review"

    review_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    review_score = db.Column(db.Integer, nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey("card.card_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    reviewed_on = db.Column(db.DateTime, server_default=func.now())

