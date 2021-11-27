from typing import List, Optional
from flask import Blueprint, session, request, g
from flashcard.models import error
from flashcard.models.error import APIException, APIErrorModel
from flashcard.models.response import APIResponse
from flashcard.models.schema import Deck, Tag, Review, Card
from flashcard.core import sanitizer
from pydantic import BaseModel, validator
from flask_pydantic import validate
from flashcard.core import db
from sqlalchemy import desc
import datetime
import pandas as pd


class CardResponseModel(BaseModel):
    card_id: int
    card_front: str
    card_back: str 

    class Config:
        orm_mode = True


class CardRequest(BaseModel):
    card_id: Optional[int]
    card_front: str
    card_back: str

    @validator("card_front")
    def validate_front(cls, val):
        val = sanitizer.sanitize(val.strip())
        assert len(val) > 0, "card_font cannot be empty"

        return val
    
    @validator("card_back")
    def validator(cls, val):
        val = sanitizer.sanitize(val.strip())
        assert len(val) > 0, "card_back cannot be empty"

        return val

class CardDeleteRequest(BaseModel):
    card_ids: List[int]
        

card_blueprint = Blueprint("card", __name__, url_prefix="/card")


@card_blueprint.get("/<int:deck_id>/")
@validate()
def get_deck_cards(deck_id: int) -> APIResponse:
    deck = Deck.query.where(Deck.deck_id == deck_id, Deck.user == g.user).first()
    if deck is None:
        raise APIException(APIErrorModel(error_code="DECK404", error_description="Deck not found"), status_code=404)

    cards = Card.query.where(Card.deck_id == deck_id).all()
    
    return APIResponse(success=True, data=[CardResponseModel.from_orm(i) for i in cards])


@card_blueprint.put("/<int:deck_id>/")
@validate()
def add_card_to_deck(body: CardRequest, deck_id: int):
    deck = Deck.query.where(Deck.deck_id == deck_id, Deck.user == g.user).first()
    if deck is None:
        raise APIException(APIErrorModel(error_code="DECK404", error_description="Deck not found"), status_code=404)
    
    card = Card(deck=deck, card_front=body.card_front, card_back=body.card_back)
    db.session.add(card)
    db.session.commit()

    return APIResponse(success=True, data=CardResponseModel.from_orm(card))


@card_blueprint.delete("/<int:deck_id>/")
@validate()
def delete_card_from_deck(body: CardDeleteRequest, deck_id: int) -> APIResponse:
    deck = Deck.query.where(Deck.deck_id == deck_id, Deck.user == g.user).first()
    if deck is None:
        raise APIException(APIErrorModel(error_code="DECK404", error_description="Deck not found"), status_code=404)

    if len(body.card_ids) < 1:
        return APIResponse(success=False, data=None)

    if Card.query.where(Card.card_id.in_(body.card_ids), Card.deck == deck).count() != len(body.card_ids):
        raise APIException(APIErrorModel(error_code="CARD101", error_description="One or more card id is not found under current deck"), status_code=400)

    db.session.execute(Card.__table__.delete().where(Card.card_id.in_(body.card_ids)))
    db.session.commit()

    return APIResponse(success=True, data={'card_ids': body.card_ids})


@card_blueprint.patch("/<int:deck_id>/")
@validate()
def update_card(body: CardRequest, deck_id: int) -> APIResponse:
    deck = Deck.query.where(Deck.deck_id == deck_id, Deck.user == g.user).first()
    card = Card.query.where(Card.card_id == body.card_id, Card.deck == deck).first()

    if deck is None or card is None:
        raise APIException(APIErrorModel(error_code="CARD404", error_description="CARD not found"), status_code=404)
    
    card.card_front = body.card_front
    card.card_back = body.card_back

    db.session.add(card)
    db.session.commit()

    return APIResponse(success=True, data=CardResponseModel.from_orm(card))


@card_blueprint.post("/<int:deck_id>/")
@validate()
def import_csv(deck_id: int) -> APIResponse:
    deck = Deck.query.where(Deck.deck_id == deck_id, Deck.user == g.user).first()
    if deck is None:
        raise APIException(APIErrorModel(error_code="DECK404", error_description="Deck not found"), status_code=404)

    file = request.files.get("file")
    if file is None:
        raise APIException(APIErrorModel(error_code="IMPORT404", error_description="No valid csv file provided"), status_code=400)
    
    try:
        df = pd.read_csv(file)[1:].values
        cards = [Card(card_front=i[0], card_back=i[1], deck=deck) for i in df]
        db.session.add_all(cards)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise APIException(APIErrorModel(error_code="IMPORT404", error_description="No valid csv file provided"), status_code=400) 

    return APIResponse(success=True, data={'count': len(cards)})
    