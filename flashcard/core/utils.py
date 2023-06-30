from typing import Union
from flask import session, redirect, url_for
from flashcard.core import cache
from flashcard.models.schema import User, Deck
from flashcard.models.error import APIException
from flashcard.models.error.user import UserNotFound, SessionExpired
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from io import BytesIO
import pandas as pd

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


def get_cache(*keys):
    key = "_".join(map(str, keys))
    return cache.get(key)

def set_cache(*keys, value):
    key = "_".join(map(str, keys))
    cache.set(key, value)

def has_cache(*keys):
    key = "_".join(map(str, keys))
    return cache.cache.has(key)




def send_mail(SUBJECT, BODY, TO, attachment = None):

    # Create message container - the correct MIME type is multipart/alternative here!
    MESSAGE = MIMEMultipart('alternative')
    MESSAGE['subject'] = SUBJECT
    MESSAGE['To'] = TO
    MESSAGE['From'] = '"Flashcard no-reply" <email@me.com>' # Your name
    MESSAGE.preamble = "Your mail reader does not support the format."

    # Record the MIME type text/html.
    HTML_BODY = MIMEText(BODY, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    MESSAGE.attach(HTML_BODY)

    if attachment:
        for data, name in attachment:
            MESSAGE.attach(MIMEApplication(data, Name=name))

    # The actual sending of the e-mail
    server = smtplib.SMTP('SMTP_ADDR')

    server.set_debuglevel(0)

    # Credentials (if needed) for sending the mail
    password = ""

    server.starttls()

    try:
        server.login("email@me.com",password)
        server.sendmail("email@me.com", [TO], MESSAGE.as_string())
        server.quit()
        return True
    except:
        return False



    
