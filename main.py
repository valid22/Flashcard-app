#!env/bin/python

from datetime import datetime
from flashcard.core.config import APP_NAME
from flashcard.core import events as _e
from flashcard.core.review import get_latest_deck_review, get_deck_score
from flashcard.models.schema import User, Deck, Card
from flashcard.routes import routes_blueprint
from flashcard import event
from celery.schedules import crontab
from flask import Flask
from celery import Celery
from flashcard.core.utils import send_mail
from sqlalchemy.sql import func
import pandas as pd
from io import StringIO
from weasyprint import HTML

def create_app() -> Flask:
    app = Flask(APP_NAME, template_folder="template", static_folder="static")
    
    event.emit("before_start", app)
    app.register_blueprint(routes_blueprint)

    return app

def make_celery(app):
    #Celery configuration
    app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
    app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
    app.config['CELERYBEAT_SCHEDULE'] = {
        # Executes every minute
        'DailyRemainder-Task': {
            'task': 'daily_remainder',
            'schedule': crontab(hour=18, minute=0)
        },
        'MonthlyReport-Task': {
            'task': 'monthly_report',
            'schedule': crontab(0, 0, day_of_month='1')
        }
    }

    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery

app: Flask = create_app()
celery = make_celery(app)
template = ""
with open("report/invoice.html", "r") as file:
    template = file.read()

@celery.task(name="export_deck_task")
def export_deck(deck_id):
    deck = Deck.query.get(deck_id)
    cards = deck.cards

    df = pd.DataFrame([{
        'card_front': c.card_front,
        'card_back': c.card_back
    }
    for c in cards
    ])

    b = StringIO()
    df.to_csv(b)
    b.seek(0)

    send_mail(f"Deck Exported", f"Dear <b>{deck.user.username}<br> </b>Deck <b>{deck.deck_title}</b> has been expored to csv and the file has been attached with this email. <br><br>Flashcard Team", deck.user.email, [(b.read(), "export.csv")])

@celery.task(name="daily_remainder")
def daily_remainder_task():
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    for user in User.query.all():
        revs = [get_latest_deck_review(d) for d in Deck.query.where(Deck.user == user).all()]
        rev = max(revs) if revs else None
        if rev:
            rev = rev.replace(hour=0, minute=0, second=0, microsecond=0)
            if rev == today:
                return
        
        print(f"sending email to - {user.email}")
        send_mail(f"Flashcard - Daily Remainder", f"Dear <b>{user.username}</b>,<br> You didn't attend any reviews on your deck for the day. Please visit our app and complete your daily task review. <br><br>Flashcard Team", user.email)

@celery.task(name="monthly_report")
def monthly_report_task():
    for user in User.query.all():
        decks = user.decks
        html = ""
        for deck in decks:
            r =  Card.query.with_entities(Card.status, func.count()).where(Card.deck == deck).group_by(Card.status).all()
            progress = dict(learning=0, learnt=0, relearning=0)
            progress.update(dict(r))
            score = round(progress['learnt'] * 100 / (sum(progress.values()) or 1), 2)
            html += f"<tr><td>{deck.deck_id}</td><td>{deck.deck_title}</td><td>{get_deck_score(deck)}</td><td>{score} %</td><td>{get_latest_deck_review(deck).strftime('%d %b, %Y %H:%M')}</td></tr>"

        h = HTML(string=template.format(username=user.username, date=datetime.now(), report_html=html), base_url="report")
        pdf = h.write_pdf()
        send_mail(f"Flashcard - Monthly Report", f"Dear <b>{user.username}</b>,<br> Please find the attached PDF containing a summary of your month' progress in Flashcard app. <br><br>Flashcard Team", user.email, [(pdf, "Report.pdf")])

if __name__ == "__main__":
    # start beat: celery -A main.celery beat --loglevel=INFO
    # start worker: celery -A main.celery worker --loglevel=info
    app.run(load_dotenv=False, port=8000, threaded=True)