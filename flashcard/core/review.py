from sqlalchemy.sql.expression import label
from flashcard.models.schema import Card, Deck, Review
from flashcard.core import db, cache
from flashcard.core.utils import get_cache, set_cache, has_cache
from sqlalchemy import desc, func
from datetime import date, timedelta, datetime
from dateutil import parser
import plotly
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import json


class ReviewLogicConfig:
    # "New Cards" tab
    NEW_STEPS = [1, 10]  # in minutes
    GRADUATING_INTERVAL = 1  # in days
    EASY_INTERVAL = 4  # in days
    STARTING_EASE = 250  # in percent

    # "Reviews" tab
    EASY_BONUS = 130  # in percent
    INTERVAL_MODIFIER = 100  # in percent
    MAXIMUM_INTERVAL = 36500  # in days

    # "Lapses" tab
    LAPSES_STEPS = [10]  # in minutes
    NEW_INTERVAL = 70  # in percent
    MINIMUM_INTERVAL = 1  # in days


def schedule_review(card: Card, response: str) -> timedelta:
    """Returns a timedelta for next review based on current response

    Args:
        card (Card): Card
        response (str): 'again', 'good', 'hard' or 'easy'

    Raises:
        ValueError: 

    Returns:
        timedelta: 
    """


    if card.status == 'learning':
        # for learning cards, there is no "hard" response possible
        if response == "again":
            card.steps_index = 0
            return timedelta(minutes=ReviewLogicConfig.NEW_STEPS[card.steps_index])
        elif response == "good":
            card.steps_index += 1
            if card.steps_index < len(ReviewLogicConfig.NEW_STEPS):
                return timedelta(minutes=ReviewLogicConfig.NEW_STEPS[card.steps_index])
            else:
                # card graduated!
                card.status = 'learnt'
                card.interval = ReviewLogicConfig.GRADUATING_INTERVAL
                return timedelta(days=card.interval)
        elif response == "easy":
            card.status = 'learnt'
            card.interval = ReviewLogicConfig.EASY_INTERVAL
            return timedelta(days=ReviewLogicConfig.EASY_INTERVAL)
        else:
            raise ValueError("invalid response")
    elif card.status == 'learnt':
        if response == "again":
            card.status = 'relearning'
            card.steps_index = 0
            card.ease_factor = max(130, card.ease_factor - 20)
            card.interval = max(ReviewLogicConfig.MINIMUM_INTERVAL, card.interval * ReviewLogicConfig.NEW_INTERVAL/100)
            return timedelta(minutes=ReviewLogicConfig.LAPSES_STEPS[0])
        elif response == "hard":
            card.ease_factor = max(130, card.ease_factor - 15)
            card.interval = card.interval * 1.2 * ReviewLogicConfig.INTERVAL_MODIFIER/100
            return timedelta(days=min(ReviewLogicConfig.MAXIMUM_INTERVAL, card.interval))
        elif response == "good":
            card.interval = (card.interval * card.ease_factor/100
                             * ReviewLogicConfig.INTERVAL_MODIFIER/100)
            return timedelta(days=min(ReviewLogicConfig.MAXIMUM_INTERVAL, card.interval))
        elif response == "easy":
            card.ease_factor += 15
            card.interval = (card.interval * card.ease_factor/100
                             * ReviewLogicConfig.INTERVAL_MODIFIER/100 * ReviewLogicConfig.EASY_BONUS/100)
            return timedelta(days=min(ReviewLogicConfig.MAXIMUM_INTERVAL, card.interval))
        else:
            raise ValueError("invalid response")
    elif card.status == 'relearning':
        if response == "again":
            card.steps_index = 0
            return timedelta(minutes=ReviewLogicConfig.LAPSE_STEPS[0])
        elif response == "good":
            card.steps_index += 1
            if card.steps_index < len(ReviewLogicConfig.LAPSE_STEPS):
                return timedelta(minutes=ReviewLogicConfig.LAPSE_STEPS[card.steps_index])
            else:
                # we have re-graduated!
                card.status = 'learnt'
                # we don't modify the interval here because that was already done when
                # going from 'learnt' to 'relearning'
                return timedelta(days=card.interval)
        else:
            raise ValueError("invalid response")


def get_latest_deck_review(deck: Deck, update: bool = False) -> datetime:
    """Get date of last review of cards from this deck

    Args:
        deck_id (int): deck id

    Returns:
        datetime.datetime
    """

    if not update and has_cache('last_review', deck.deck_id):
        val = get_cache("last_review", deck.deck_id)
        return parser.parse(val) if val else deck.created_on

    query = Review.query.with_entities(Review.reviewed_on).where(Review.deck == deck).order_by(desc(Review.reviewed_on)).limit(1)
    #db.session.query(Review.reviewed_on).join(Card, Review.card).filter(Card.deck == deck).order_by(desc(Review.reviewed_on)).limit(1)
    review_date = query.scalar()
    
    val = review_date or deck.created_on
    set_cache("last_review", deck.deck_id, value=val.isoformat())
    return val


def get_deck_score(deck: Deck, update: bool = False) -> int:
    if not update and has_cache("deck_score", deck.deck_id):
        return int(get_cache("deck_score", deck.deck_id))

    r =  Card.query.with_entities(Card.status, func.count()).where(Card.deck == deck).group_by(Card.status).all()
    res = dict(learning=0, learnt=0, relearning=0) # | dict(res)
    res.update(dict(r))
    total = sum(res.values()) or 1

    score = (res['learnt'] * 1 + res['learning'] * 0 - res['relearning'] * 1) / total
    val = round(score, 2) * 100
    set_cache("deck_score", deck.deck_id, value=val)
    return val


def get_score_plot_data(deck: Deck) -> str:
    reviews = deck.reviews
    if reviews:
        df = pd.DataFrame({'x': list(range(len(reviews))), 'y': [i.review_score for i in reviews]})
    else:
        df = pd.DataFrame({'x': [get_latest_deck_review(deck)], 'y':[get_deck_score(deck)]})
        
    data = [
        px.area(
            x=df['x'],
            y=df['y'],
            title='Deck score overtime',
            labels={'x': 'Attempt', 'y': 'Score'}
        )
    ]
    graphJSON = json.dumps(data[0], cls=plotly.utils.PlotlyJSONEncoder)
    
    return graphJSON