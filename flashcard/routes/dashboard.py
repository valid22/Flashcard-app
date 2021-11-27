from operator import or_
from flask import Blueprint, render_template, url_for, redirect, session, request, g
from flashcard.models.error import APIException
from flashcard.models.schema import Deck, Card, Review
from flashcard.core.utils import get_current_user
from flashcard.core.review import schedule_review
from flashcard.routes.api.deck import DeckResponseModel
from flashcard.core.review import get_latest_deck_review, get_deck_score, get_score_plot_data
from pydantic import ValidationError
from sqlalchemy import exc
from sqlalchemy.sql import func
from flashcard.core import db
import datetime

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
    deck_id = request.args.get("deck")
    deck = Deck.query.where(Deck.user == g.user).first() if deck_id is None else Deck.query.where(Deck.user == g.user, Deck.deck_id == deck_id).first()
    print(deck_id, deck)
    decks = Deck.query.with_entities(Deck.deck_id, Deck.deck_title).where(Deck.user == g.user).all()
    if deck is not None:
        return render_template("dashboard/home.html", user=g.user, plot_data = get_score_plot_data(deck), deck=deck, last_review=get_latest_deck_review(deck).strftime("%d %b, %Y %H:%M:%S"), decks=decks)
    else:
        return render_template("dashboard/home.html", user=g.user, plot_data = None)


@dashboard_blueprint.get("/deck/")
def deck():
    return render_template("dashboard/deck.html", user=g.user)


@dashboard_blueprint.get("/deck/<int:deck_id>/")
def deck_cards(deck_id: int):    
    return render_template("dashboard/cards.html", user=g.user, deck = db.session.query(Deck).where(Deck.user == g.user, Deck.deck_id == deck_id).first())


@dashboard_blueprint.get("/review/")
def review():
    decks = []
    for d in (g.user.decks or []):
        r =  Card.query.with_entities(Card.status, func.count()).where(Card.deck == d).group_by(Card.status).all()
        progress = dict(learning=0, learnt=0, relearning=0) # | dict(res)
        progress.update(dict(r))
        decks.append(DeckResponseModel(deck_id = d.deck_id, deck_title=d.deck_title, deck_tags=[], created_on=d.created_on.strftime("%d %b, %Y"), 
            last_reviewed_on=get_latest_deck_review(d).strftime("%d %b, %Y %H:%M:%S"), cards_count=-1, review_score=get_deck_score(d), progress=progress))

    return render_template("dashboard/review.html", user=g.user, decks=decks)

@dashboard_blueprint.get("/review/<int:deck_id>")
def review_deck(deck_id: int):
    deck = db.session.query(Deck).where(Deck.user == g.user, Deck.deck_id == deck_id).first()
    if deck is None:
        return redirect(url_for('.review'))
    
    card = Card.query.where(Card.deck==deck, Card.next_review <= datetime.datetime.now()).order_by(func.random()).first()
    
    return render_template("/dashboard/review_card.html", user=g.user, card=card, deck=deck)

@dashboard_blueprint.post("/review/<int:deck_id>")
def review_deck_response(deck_id: int):
    deck = db.session.query(Deck).where(Deck.user == g.user, Deck.deck_id == deck_id).first()
    if deck is None:
        return redirect(url_for('.review'))

    card_id = request.form.get("card_id")
    r = request.form.get("response")
    card = Card.query.where(Card.deck == deck, Card.card_id == card_id).first()
    if card is None:
        return redirect(url_for('.review'))
    
    rint = schedule_review(card, r)
    
    card.last_reviewed = datetime.datetime.now()
    card.next_review = card.last_reviewed + rint

    review = Review(review_score=get_deck_score(deck), deck=deck, reviewed_on=card.last_reviewed)

    db.session.add(card)
    db.session.add(review)
    db.session.commit()
    
    return redirect(url_for('.review_deck', deck_id=deck_id))