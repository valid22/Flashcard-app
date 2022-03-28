from flask import Blueprint, g
from flask_cors import CORS
from sqlalchemy import exc

from flashcard.core import db
from flashcard.models.error import APIErrorModel, APIExceptionResponse, APIException
from flashcard.models.response import APIResponse
from flashcard.core.utils import get_current_user
from flashcard.routes.api.v2.auth import auth_blueprint
from flashcard.routes.api.v2.review import review_blueprint
from flashcard.routes.api.v2.deck import deck_blueprint
from flashcard.routes.api.v2.card import card_blueprint

apiv2_blueprint = Blueprint("apiv2", __name__, url_prefix="/api/v2/")
apiv2_blueprint.register_blueprint(auth_blueprint)
apiv2_blueprint.register_blueprint(review_blueprint)
apiv2_blueprint.register_blueprint(deck_blueprint)
apiv2_blueprint.register_blueprint(card_blueprint)
CORS(apiv2_blueprint, allow_headers='*', origins=['http://localhost:8080'])

@apiv2_blueprint.errorhandler(exc.SQLAlchemyError)
def handle_db_exceptions(error):
    db.session.rollback()
    
    return APIResponse(success=False, data=None, errors=[APIErrorModel(error_code="SERVER_101", error_description="Something went wrong", status_code=500)]).json(), 500


@apiv2_blueprint.errorhandler(APIException)
def handle_api_exception(error: APIException):
    resp = APIResponse(success=False, data=None, errors=error.errors.errors)
    return resp.json(), error.errors.status_code

