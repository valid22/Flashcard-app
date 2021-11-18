from flask import Blueprint, session, request, g
from flashcard.models.error import APIException, APIErrorModel
from flashcard.models.response import APIResponse
from flashcard.models.request.deck import CreateDeckRequest
from flashcard.models.response.deck import DeckResponseModel
from flashcard.models.schema import Deck, Tag, Review, Card
from pydantic import ValidationError
from flask_pydantic import validate
from flashcard.core import db
from sqlalchemy import desc
import datetime


deck_blueprint = Blueprint("deck", __name__, url_prefix="/deck")


def get_latest_deck_review(deck: Deck) -> datetime.datetime:
    """Get date of last review of cards from this deck

    Args:
        deck_id (int): deck id

    Returns:
        datetime.datetime
    """

    query = db.session.query(Review.reviewed_on).join(Card, Review.card).filter(Card.deck == deck).order_by(desc(Review.reviewed_on)).limit(1)
    review_date = query.scalar()
    
    return review_date or deck.created_on


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
def get_user_decks():
    q = db.session.query(Deck, db.func.count(Deck.cards)).select_from(Deck).outerjoin(Card).where(Deck.user == g.user).group_by(Deck.deck_id)
    
    return APIResponse(success=True, data=[
        DeckResponseModel(deck_id = d.deck_id, deck_title=d.deck_title, deck_tags=[i.tag for i in d.tags], created_on=d.created_on.strftime("%d %b, %Y"), 
            last_reviewed_on=get_latest_deck_review(d).strftime("%d %b, %Y"), cards_count=count)

        for d, count in q if d is not None
    ])    


@deck_blueprint.delete("/<int:deck_id>/")
@validate()
def delete_deck(deck_id: int):
    deck = db.session.query(Deck).where(Deck.user == g.user, Deck.deck_id == deck_id).first()
    if deck is None:
        raise APIException(APIErrorModel(error_code="DECK404", error_description="Deck not found"), status_code=404)

    db.session.delete(deck)
    db.session.commit()

    return APIResponse(success=True, data={'deck_id': deck_id})