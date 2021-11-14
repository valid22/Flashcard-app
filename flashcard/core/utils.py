from typing import Union
from flask import session, redirect, url_for
from flashcard.models.schema import User
from flashcard.models.error import APIException
from flashcard.models.error.user import UserNotFound, SessionExpired

def get_current_user_id() -> Union[int, None]:
    """Returns the current session's user id .

    Returns:
        Union[int, None]: user id
    """
    
    return session.get('user_id', None)

def get_current_user() -> User:
    """Get the current user object.

    Raises:
        APIException: SessionExpired
        APIException: UserNotFound

    Returns:
        User: User mobject
    """

    uid = get_current_user_id()
    
    if uid is None:
        raise APIException(SessionExpired())
    
    user = User.query.get(uid)
    if user is None:
        raise APIException(UserNotFound())
    
    return user

