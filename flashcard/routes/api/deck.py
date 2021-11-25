from flask import Blueprint, session, request, g
from flashcard.models.error import APIException, APIErrorModel
from flashcard.models.response import APIResponse
from flashcard.models.schema import Deck, Tag, Review, Card
from flashcard.core.review import get_latest_deck_review
from pydantic import BaseModel, validator
from typing import List, Set, Union
from flask_pydantic import validate
from flashcard.core import db
from sqlalchemy import desc
import datetime

class CreateDeckRequest(BaseModel):
    name: str 
    tags: Union[str, Set[str]]

    @validator("tags")
    def validate_tags(cls, val):
        val = val.strip()
        if not val:
            return set()

        if isinstance(val, str):
            val = val.split(",")
        
        assert isinstance(val, list), "tags should be a list separated by comma"
        val = set(i.strip().lower() for i in val)

        assert len(val) < 5, "can assign a maximum of 4 tags to a deck"

        for tag in val:
            assert 1 <= len(tag) <= 12, "tag can be a maximum of 12 chars long"
        
        return val
    
    @validator("name")
    def validate_name(cls, val):
        assert isinstance(val, str), "name should be a valid string"
        assert 1 <= len(val) <= 120, "name can be a maximum of 120 chars long"

        return val

class DeckResponseModel(BaseModel):
    deck_id: int
    deck_title: str 
    deck_tags: List[str]
    created_on: str
    last_reviewed_on: str
    cards_count: int
    review_score: int = -1


deck_blueprint = Blueprint("deck", __name__, url_prefix="/deck")

@deck_blueprint.put("/")
@validate()
def create_new_deck(body: CreateDeckRequest) -> APIResponse:
    d = Deck(deck_title=body.name, user=g.user)

    tags = Tag.query.where(Tag.tag.in_(body.tags)).all()
    rtags = body.tags - set(i.tag for i in tags)
    
    for tag in rtags:
        t = Tag(tag=tag)
        db.session.add(t)
        tags.append(t)

    d.tags = tags

    db.session.add(d)
    db.session.commit()    

    return APIResponse(success=True, 
        data = DeckResponseModel(deck_id = d.deck_id, deck_title=d.deck_title, deck_tags=[i.tag for i in d.tags], created_on=d.created_on.strftime("%d %b, %Y"), 
            last_reviewed_on=get_latest_deck_review(d).strftime("%d %b, %Y"), cards_count=0)
    )


@deck_blueprint.get("/")
@validate()
def get_user_decks() -> APIResponse:
    q = db.session.query(Deck, db.func.count(Deck.cards)).select_from(Deck).outerjoin(Card).where(Deck.user == g.user).group_by(Deck.deck_id)
    
    return APIResponse(success=True, data=[
        DeckResponseModel(deck_id = d.deck_id, deck_title=d.deck_title, deck_tags=[i.tag for i in d.tags], created_on=d.created_on.strftime("%d %b, %Y"), 
            last_reviewed_on=get_latest_deck_review(d).strftime("%d %b, %Y"), cards_count=count)

        for d, count in q if d is not None
    ])    


@deck_blueprint.delete("/<int:deck_id>/")
@validate()
def delete_deck(deck_id: int) -> APIResponse:
    deck = db.session.query(Deck).where(Deck.user == g.user, Deck.deck_id == deck_id).first()
    if deck is None:
        raise APIException(APIErrorModel(error_code="DECK404", error_description="Deck not found"), status_code=404)

    db.session.delete(deck)
    db.session.commit()

    return APIResponse(success=True, data={'deck_id': deck_id})