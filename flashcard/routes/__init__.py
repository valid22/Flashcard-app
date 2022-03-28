from flask import Blueprint, render_template, url_for, redirect
from flashcard.models.error import APIException
from flashcard.core.utils import get_current_user
from flashcard.routes import api

from flashcard.routes.login import login_blueprint
from flashcard.routes.dashboard import dashboard_blueprint
from flashcard.routes.api import api_blueprint
from flashcard.routes.api.v2 import apiv2_blueprint

routes_blueprint = Blueprint("routes", __name__, url_prefix="/")
#routes_blueprint.register_blueprint(login_blueprint)
#routes_blueprint.register_blueprint(dashboard_blueprint)
#routes_blueprint.register_blueprint(api_blueprint)
routes_blueprint.register_blueprint(apiv2_blueprint)

@routes_blueprint.route("/")
def index():
    try:
        get_current_user()
        return redirect(url_for("routes.dashboard.dashboard"))
    except APIException:
        return redirect(url_for("routes.login.login"))

