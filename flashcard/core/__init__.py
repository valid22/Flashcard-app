from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from html_sanitizer import Sanitizer
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_caching import Cache 

db = SQLAlchemy()
sess = Session()
sanitizer = Sanitizer()
jwt = JWTManager()
cache = Cache(config={
    'CACHE_TYPE': 'redis',
    'CACHE_KEY_PREFIX': 'flashcard',
})
