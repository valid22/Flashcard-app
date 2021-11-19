from flask import Blueprint, render_template, url_for, redirect, session, request, g
from flashcard.models.error import APIException
from flashcard.models.schema import Deck
from flashcard.core.utils import get_current_user
from pydantic import ValidationError
from sqlalchemy import exc
from flashcard.core import db
import json

dashboard_blueprint = Blueprint("dashboard", __name__, url_prefix="/dashboard")

@dashboard_blueprint.before_request
def requires_login():
    try:
        user = get_current_user()
    except APIException:
        return redirect(url_for('routes.login.login'))
    
    g.user = user

@dashboard_blueprint.get("/")
def dashboard():
    return render_template("dashboard/home.html", user=g.user)


@dashboard_blueprint.get("/deck")
def deck():
    return render_template("dashboard/deck.html", user=g.user)


@dashboard_blueprint.get("/deck/<int:deck_id>/")
def deck_cards(deck_id: int):    
    return render_template("dashboard/cards.html", user=g.user, deck = db.session.query(Deck).where(Deck.user == g.user, Deck.deck_id == deck_id).first())
