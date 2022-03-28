from datetime import datetime, timedelta
from tokenize import Token
from typing import List, Optional
from flask import Blueprint, session, request, g, jsonify
from flask_cors import cross_origin
from flashcard.models.error import APIException, APIErrorModel
from flashcard.models.response import APIResponse
from flashcard.core.review import get_latest_deck_review, get_deck_score
from flask_pydantic import validate
from sqlalchemy import func
from flashcard.models.schema import Review, Deck, User, Card
from pydantic import BaseModel, validator, ValidationError, constr
from flashcard.core import db, jwt
import hashlib
from base64 import b64decode

from flask_jwt_extended import current_user, jwt_required, get_jwt

deck_blueprint = Blueprint("deck", __name__, url_prefix="/deck")

class CreateDeckRequest(BaseModel):
    name: str 
    img: constr(max_length=6670 + 22)

    @validator("img")
    def validate_tags(cls, val):
        val = val.strip()
        assert val, "Image cannot be empty"

        if val == "default":
            return "default"

        b64 = val.split("base64,")[1]
        try:
            b64decode(b64)
        except:
            raise Exception("Image should be a valid PNG file")

        return val
    
    @validator("name")
    def validate_name(cls, val):
        assert isinstance(val, str), "name should be a valid string"
        assert val, "name cannot be empty"
        assert 1 <= len(val) <= 120, "name can be a maximum of 120 chars long"

        return val

class UpdateDeckRequest(BaseModel):
    deck_title: str

class DeckResponseModel(BaseModel):
    deck_id: int
    deck_title: str 
    deck_img: str
    deck_tags: List[str]
    created_on: str
    last_reviewed_on: str
    last_review: datetime
    cards_count: int
    review_score: int = -1
    progress: Optional[dict]


@deck_blueprint.get("/list")
@jwt_required()
@validate()
def create_user() -> APIResponse:
    user = current_user
    deck = db.session.query(Deck.deck_id, Deck.deck_title, Deck.deck_img).where(Deck.user == user).all()

    return APIResponse(
        success=True,
        data=[
            {
                'id': d[0],
                'title': d[1],
                'last_review': db.session.query(Review.reviewed_on).where(Review.deck_id == d[0]).order_by(Review.reviewed_on.desc()).limit(1).scalar(),
            }

            for d in deck
        ],
    )


@deck_blueprint.put("/")
@jwt_required()
@validate()
def create_new_deck(body: CreateDeckRequest) -> APIResponse:
    user = current_user
    d = Deck(deck_title=body.name, user=user)
    d.tags = []
    d.deck_img = body.img

    db.session.add(d)
    db.session.commit()    
    r = get_latest_deck_review(d)
    return APIResponse(success=True, 
        data = DeckResponseModel(deck_id = d.deck_id, deck_title=d.deck_title, deck_tags=[i.tag for i in d.tags], created_on=d.created_on.strftime("%d %b, %Y"), 
            last_reviewed_on=r.strftime("%d %b, %Y"), last_review=r, cards_count=0, deck_img=d.deck_img or 'default')
    )


@deck_blueprint.patch("/<int:deck_id>")
@jwt_required()
@validate()
def update_deck(body: UpdateDeckRequest, deck_id: int) -> APIResponse:
    user = current_user
    deck = db.session.query(Deck).where(Deck.user == user, Deck.deck_id == deck_id).first()
    deck.deck_title = body.deck_title

    db.session.add(d)
    db.session.commit()    
    
    return APIResponse(success=True, 
        data = {
            'deck_id': deck_id,
            'deck_title': body.deck_title
        }
    )


@deck_blueprint.get("/")
@jwt_required()
@validate()
def get_user_decks() -> APIResponse:
    user = current_user
    q = db.session.query(Deck, db.func.count(Deck.cards)).select_from(Deck).outerjoin(Card).where(Deck.user == user).group_by(Deck.deck_id)
    
    return APIResponse(success=True, data=[
        DeckResponseModel(deck_id = d.deck_id, deck_title=d.deck_title, deck_tags=[i.tag for i in d.tags], created_on=d.created_on.strftime("%d %b, %Y"), 
            last_reviewed_on=get_latest_deck_review(d).strftime("%d %b, %Y"), cards_count=count, deck_img=d.deck_img or 'default', last_review=get_latest_deck_review(d))

        for d, count in q if d is not None
    ])    


@deck_blueprint.delete("/<int:deck_id>/")
@jwt_required()
@validate()
def delete_deck(deck_id: int) -> APIResponse:
    user = current_user
    deck = db.session.query(Deck).where(Deck.user == user, Deck.deck_id == deck_id).first()
    if deck is None:
        raise APIException(APIErrorModel(error_code="DECK404", error_description="Deck not found"), status_code=404)

    db.session.delete(deck)
    db.session.commit()

    return APIResponse(success=True, data={'deck_id': deck_id})


@deck_blueprint.get("/<int:deck_id>/")
@jwt_required()
@validate()
def get_deck_data(deck_id: int) -> APIResponse:
    user = current_user
    deck = db.session.query(Deck).where(Deck.user == user, Deck.deck_id == deck_id).first()
    if deck is None:
        raise APIException(APIErrorModel(error_code="DECK404", error_description="Deck not found"), status_code=404)

    r = get_latest_deck_review(deck)
    cc = db.session.query(Card).where(Card.deck == deck).with_entities(func.count()).scalar()
    return APIResponse(success=True, 
        data = DeckResponseModel(deck_id = deck.deck_id, deck_title=deck.deck_title, deck_tags=[], created_on=deck.created_on.strftime("%d %b, %Y"), 
            last_reviewed_on=r.strftime("%d %b, %Y"), last_review=r, cards_count=cc, deck_img=deck.deck_img or 'default'), review_score=get_deck_score(deck)
    )

@deck_blueprint.get("/<int:deck_id>/export/")
@jwt_required()
@validate()
def export_deck(deck_id: int) -> APIResponse:
    from main import export_deck
    user = current_user
    deck = db.session.query(Deck).where(Deck.user == user, Deck.deck_id == deck_id).first()
    if deck is None:
        raise APIException(APIErrorModel(error_code="DECK404", error_description="Deck not found"), status_code=404)
    
    export_deck.delay(deck_id)
    return APIResponse(success=True, 
        data='started'
    )