from flask import Blueprint, session, request, g
from flashcard.models.error import APIException
from flashcard.models.response import APIResponse
from flashcard.models.request.deck import CreateDeckRequest
from flashcard.models.response.deck import DeckResponseModel
from flashcard.models.schema import Deck, Tag
from pydantic import ValidationError
from flask_pydantic import validate
from flashcard.core import db


deck_blueprint = Blueprint("deck", __name__, url_prefix="/deck")

@deck_blueprint.route("/", methods=['PUT'])
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
        data = DeckResponseModel(deck_id = d.deck_id, deck_title=d.deck_title, deck_tags=[i.tag for i in d.tags])
    )

    