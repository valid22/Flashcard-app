from flashcard import event
from flashcard.core.config import *
from flashcard.core import db
from flashcard.core.log import InterceptHandler
from flashcard.models import schema

from flask import Flask
from flask.logging import default_handler
from loguru import logger
import logging
import sys


@event.on("before_start")
def pre_process(app: Flask) -> None:
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_ECHO'] = SQLALCHEMY_ECHO
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['TOKEN_HEADER'] = "Authorization"
    app.config['ENV'] = 'development'

    logger.info("initialized app config values")

@event.on("before_start")
def intercept_log(app: Flask) -> None:
    logger.remove()
    logger.add(LOG_FILE, level=LOG_LEVEL, format="{time} | {level} | {name}.{function}:{line} | {message}",
                 backtrace=LOG_BACKTRACE, rotation='5 MB', enqueue=True)
    logger.add(sys.stderr, level=LOG_LEVEL, format="<green>{time:HH:mm:ss (DD/MM)}</green> | <level>{level: <8}</level> | <level>{message}</level>",
                 backtrace=LOG_BACKTRACE, enqueue=True)
    
    #register loguru as handler
    app.logger.setLevel(LOG_LEVEL)
    logging.basicConfig(handlers=[InterceptHandler()], level=LOG_LEVEL)
    logger.info("added log intercept handler")

@event.on("before_start")
def setup_database(app: Flask) -> None:
    db.init_app(app)

    with app.app_context():
        db.create_all()

    logger.info("database setup complete")


