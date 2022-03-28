from datetime import datetime, timedelta
from tokenize import Token
from typing import List, Optional
from flask import Blueprint, session, request, g, jsonify, Response
from flask_cors import cross_origin
from flashcard.models.error import APIExceptionResponse, APIErrorModel
from flashcard.core import cache
from flashcard.models.response import APIResponse
from flask_pydantic import validate
from flashcard.models.schema import User
from pydantic import BaseModel, validator, ValidationError
from flashcard.core import db, jwt
import hashlib

from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required, get_jwt, current_user

class LoginRequest(BaseModel):
    username: str 
    password: str 

    @validator("username")
    def username_alpanum_check(cls, username):
        username = username.strip()

        assert 4 <= len(username) <= 20, "must be between 4 and 20 characters"
        assert username.isalnum(), "must be alpha-numberic"

        return username
        
    @validator("password")
    def password_validator(cls, password):
        assert 6 <= len(password), "must be at least 6 characters long"
        assert len(password) <= 20, "can contain a maximum of 20 characters"

        return hashlib.sha256(password.encode()).hexdigest()

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str]
    expires: datetime

auth_blueprint = Blueprint("auth", __name__, url_prefix="/auth")

@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.username

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.query.filter_by(username=identity).one_or_none()


@jwt.expired_token_loader
@jwt.needs_fresh_token_loader
@jwt.revoked_token_loader
@jwt.token_verification_failed_loader
@jwt.user_lookup_error_loader
def my_expired_token_callback(jwt_header, jwt_payload):
    return jsonify(APIExceptionResponse(APIErrorModel(error_code="AUTH401", error_description="Invalid OAuth token"), 401).dict()), 401

@jwt.invalid_token_loader
@jwt.unauthorized_loader
def invalid_token_response(msg):
    return jsonify(APIExceptionResponse(APIErrorModel(error_code="AUTH500", error_description=msg), 401).dict()), 401


@auth_blueprint.post("/create")
@validate()
def create_user(body: LoginRequest) -> APIResponse:
    user = User.query.where(User.username == body.username).first()
    if user is not None:
        return APIResponse(
            success=False, 
            data=None, 
            errors=[{"loc": ("username", ), "msg": "Username already exists"}]
        ), 500
    
    user = User(username=body.username, password=body.password)
    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=user, fresh=True, expires_delta=timedelta(hours=1))
    refresh_token = create_refresh_token(identity=user, expires_delta=timedelta(days=100))
    return APIResponse(
        success=True,
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires=datetime.now() + timedelta(hours=1),
        ),
    )

@auth_blueprint.post("/token")
@validate()
def get_deck_cards(body: LoginRequest) -> APIResponse:
    
    user = User.query.where(User.username == body.username).first()
    if user is None or body.password != user.password:
        return APIResponse(
            success=False, 
            data=None, 
            errors=[{"loc": ("password", ), "msg": "Incorrect password"}, {"loc": ("username", ), "msg": "Incorrect username"}]
        ), 403

    access_token = create_access_token(identity=user, fresh=True, expires_delta=timedelta(hours=1))
    refresh_token = create_refresh_token(identity=user, expires_delta=timedelta(days=100))
    return APIResponse(
        success=True,
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires=datetime.now() + timedelta(hours=1),
        ),
    )

@auth_blueprint.post("/token/refresh")
@jwt_required(refresh=True)
@validate()
def refresh():
    identity = current_user
    access_token = create_access_token(identity=identity, expires_delta=timedelta(hours=1))
    refresh_token = get_jwt()
    
    expires = datetime.utcfromtimestamp(refresh_token['exp'])
    diff = expires - datetime.now()
    if diff < timedelta(days=2):
        refresh_token = create_refresh_token(identity=identity, expires_delta=timedelta(days=100))
    else:
        refresh_token = None

    return APIResponse(
        success=True,
        data=TokenResponse(
            access_token=access_token,
            expires=datetime.now() + timedelta(hours=1),
            refresh_token=refresh_token,
        ),
    )

@auth_blueprint.get("/ping")
@jwt_required()
@validate()
def ping():
    return APIResponse(
        success=True,
        data={
            'user_id': current_user.user_id
        }
    )


def event_stream(user):
    pubsub = cache.cache.pubsub()
    pubsub.subscribe(f'notif_{user.user_id}')
    yield "test message"
    for message in pubsub.listen():
        yield message['data']


@auth_blueprint.get("/notif")
@jwt_required()
def stream():
    return Response(event_stream(current_user),
                          mimetype="text/event-stream")
