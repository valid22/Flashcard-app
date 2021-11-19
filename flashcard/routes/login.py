from flask import Blueprint, render_template, url_for, redirect, session, request
from flashcard.models.error import APIException
from flashcard.models.request.login import LoginRequest
from flashcard.models.response import APIResponse
from flashcard.models.schema import User
from pydantic import ValidationError
from sqlalchemy import exc
from flashcard.core import db
import json

login_blueprint = Blueprint("login", __name__, url_prefix="/login")


@login_blueprint.get("/")
def login():
    session['user_id'] = None 
    
    return render_template("login.html")


@login_blueprint.post("/")
def login_user():
    session['user_id'] = None # fresh login
    
    try:
        user_creds = LoginRequest(**request.form)
    except ValidationError as e:
        return render_template("login.html", errors=e.errors())
    
    user = User.query.where(User.username == user_creds.username).first()
    if user is None:
        user = User(username=user_creds.username, password=user_creds.password)
        db.session.add(user)
        db.session.commit()
    
    else:
        if user_creds.password != user.password:
            return render_template("login.html", errors=[{"loc": ("password", ), "msg": "incorrect password"}])

    session['user_id'] = user.user_id
        
    return redirect(url_for("routes.dashboard.dashboard"))
    

@login_blueprint.errorhandler(exc.SQLAlchemyError)
def handle_db_exceptions(error):
    db.session.rollback()
    
    return render_template("login.html", errors=[{"loc": ("login", ), "msg": "something went wrong during signin, please try again"}])

