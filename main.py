#!env/bin/python

from flashcard.core.config import APP_NAME
from flashcard.core import events as _e
from flashcard import event

from flask import Flask

def create_app() -> Flask:
    app = Flask(APP_NAME)
    
    event.emit("before_start", app)

    return app

app: Flask = create_app()

if __name__ == "__main__":
    app.run(debug=True, load_dotenv=False, port=8080)