from flashcard import event
from flashcard.core.config import *
from flashcard.core import db, sess, jwt, cache
from flashcard.core.log import InterceptHandler
from flashcard.models import schema

from flask import Flask
from flask.logging import default_handler
from flask_session import Session
from datetime import timedelta
from loguru import logger
import logging
import sys


@event.on("before_start")
def pre_process(app: Flask) -> None:
    """Initialize app config values

    Args:
        app (Flask): Flask app
    """

    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_ECHO'] = SQLALCHEMY_ECHO
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['ENV'] = ENV_TYPE
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config["JWT_SECRET_KEY"] = SECRET_KEY
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['TEMPLATES_AUTO_RELOAD'] = False

    logger.info("initialized app config values")

@event.on("before_start")
def intercept_log(app: Flask) -> None:
    """Add intercept handler to Flask

    Args:
        app (Flask): Flask app
    """

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
    """Setup the database

    Args:
        app (Flask): Flask app
    """

    db.init_app(app)

    with app.app_context():
        db.create_all()

    logger.info("database setup complete")

@event.on("before_start")
def setup_session(app: Flask) -> None:
    """Initialize Flask-sessions.

    Args:
        app (Flask): Flask app
    """
    
    sess.init_app(app)

    logger.info("flask-session initialized")


@event.on("before_start")
def setup_session(app: Flask) -> None:
    """Initialize JWT Manager.

    Args:
        app (Flask): Flask app
    """
    
    jwt.init_app(app)

    logger.info("Flask-JWT initialized")


@event.on("before_start")
def setup_session(app: Flask) -> None:
    """Initialize CORS.

    Args:
        app (Flask): Flask app
    """
    
    #cors.init_app(app)

    logger.info("Flask-CORS initialized")


@event.on("before_start")
def setup_session(app: Flask) -> None:
    """Initialize Cache.

    Args:
        app (Flask): Flask app
    """
    
    cache.init_app(app)

    logger.info("Flask-caching initialized")
