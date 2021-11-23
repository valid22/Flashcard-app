from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from html_sanitizer import Sanitizer

db = SQLAlchemy()
sess = Session()
sanitizer = Sanitizer()