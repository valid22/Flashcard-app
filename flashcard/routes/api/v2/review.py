from datetime import datetime, timedelta
from tokenize import Token
from typing import List, Optional
from flask import Blueprint, session, request, g, jsonify
from flask_cors import cross_origin
from flashcard.models.error import APIException, APIErrorModel
from flashcard.models.response import APIResponse
from flask_pydantic import validate
from flashcard.models.schema import Review, Deck, User, review, Card
from flashcard.core.review import schedule_review, get_deck_score, get_latest_deck_review
from pydantic import BaseModel, validator, ValidationError
from flashcard.core import db, jwt
import hashlib
from sqlalchemy.sql import func

from flask_jwt_extended import current_user, jwt_required, get_jwt

review_blueprint = Blueprint("review", __name__, url_prefix="/review")

class DeckReviewModel(BaseModel):
    review_score: int
    reviewed_on: datetime

    class Config:
        orm_mode = True

class CardResponseModel(BaseModel):
    card_id: int
    card_front: str
    card_back: str 
    status: str

    class Config:
        orm_mode = True

@review_blueprint.get("/<int:deck_id>")
@jwt_required()
@validate()
def create_user(deck_id: int) -> APIResponse:
    user = current_user
    deck = db.session.query(Deck).where(Deck.user == user, Deck.deck_id == deck_id).first()
    if deck is None:
        raise APIException(APIErrorModel(error_code="DECK404", error_description="Deck not found"), status_code=404)
    
    reviews = Review.query.where(Review.deck == deck).order_by(Review.reviewed_on.desc()).limit(100).all()
    _sum = 0
    d = []
    for r in reviews:
        d.append(DeckReviewModel.from_orm(r))
        _sum += r.review_score

    return APIResponse(
        success=True,
        data=d if _sum > 0 else [],
    )


@review_blueprint.get("/cards/<int:deck_id>/")
@jwt_required()
@validate()
def get_next_review(deck_id: int) -> APIResponse:
    print("lol")
    user = current_user
    deck = db.session.query(Deck).where(Deck.user == user, Deck.deck_id == deck_id).first()
    if deck is None:
        return APIException(APIErrorModel(error_code="DECK404", error_description="Deck not found"), status_code=404)
    
    card = Card.query.where(Card.deck==deck, Card.next_review <= datetime.now()).order_by(func.random()).first()
    r =  Card.query.with_entities(Card.status, func.count()).where(Card.deck == deck).group_by(Card.status).all()
    progress = dict(learning=0, learnt=0, relearning=0) # | dict(res)
    progress.update(dict(r))
    
    return APIResponse(
        success=True,
        data={
            'review': CardResponseModel.from_orm(card) if card else None,
            'progress': round(progress['learnt'] * 100 / (sum(progress.values()) or 1), 1),
        }
    )

@review_blueprint.post("/cards/<int:deck_id>/")
@jwt_required()
@validate()
def review_card(deck_id: int) -> APIResponse:
    user = current_user
    deck = db.session.query(Deck).where(Deck.user == user, Deck.deck_id == deck_id).first()
    if deck is None:
        raise APIException(APIErrorModel(error_code="DECK404", error_description="Deck not found"), status_code=404)

    card_id = request.json.get("card_id")
    r = request.json.get("response")
    card = Card.query.where(Card.deck == deck, Card.card_id == card_id).first()
    if card is None:
        raise APIException(APIErrorModel(error_code="CARD404", error_description="Card not found"), status_code=404)
    
    rint = schedule_review(card, r)
    
    card.last_reviewed = datetime.now()
    card.next_review = card.last_reviewed + rint

    review = Review(review_score=get_deck_score(deck, update=True), deck=deck, reviewed_on=card.last_reviewed)
    get_latest_deck_review(deck, update=True)

    db.session.add(card)
    db.session.add(review)
    db.session.commit()

    card = Card.query.where(Card.deck==deck, Card.next_review <= datetime.now()).order_by(func.random()).first()
    r =  Card.query.with_entities(Card.status, func.count()).where(Card.deck == deck).group_by(Card.status).all()
    progress = dict(learning=0, learnt=0, relearning=0) # | dict(res)
    progress.update(dict(r))
    
    return APIResponse(
        success=True,
        data={
            'review': CardResponseModel.from_orm(card) if card else None,
            'progress': round(progress['learnt'] * 100 / (sum(progress.values())), 1),
        }
    )
    