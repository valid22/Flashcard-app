from flask import Blueprint, g
from sqlalchemy import exc

from flashcard.core import db
from flashcard.models.error import APIErrorModel, APIExceptionResponse, APIException
from flashcard.models.response import APIResponse
from flashcard.core.utils import get_current_user
from flashcard.routes.api.deck import deck_blueprint
from flashcard.routes.api.card import card_blueprint

api_blueprint = Blueprint("api", __name__, url_prefix="/api")
api_blueprint.register_blueprint(deck_blueprint)
api_blueprint.register_blueprint(card_blueprint)

@api_blueprint.before_request
def requires_login():
    try:
        user = get_current_user()
    except APIException:
        raise APIException(APIErrorModel(error_code="USER403", error_description="Permission denied.", status_code=403), status_code=403)
    
    g.user = user
    

@api_blueprint.errorhandler(exc.SQLAlchemyError)
def handle_db_exceptions(error):
    db.session.rollback()
    
    return APIResponse(success=False, data=None, errors=[APIErrorModel(error_code="SERVER_101", error_description="Something went wrong", status_code=500)]).json(), 500


@api_blueprint.errorhandler(APIException)
def handle_api_exception(error: APIException):
    resp = APIResponse(success=False, data=None, errors=error.errors.errors)
    return resp.json(), error.errors.status_code
