from flashcard.models.error import APIErrorModel

class UserNotFound(APIErrorModel):
    error_code: str = "USER_101"
    error_description: str = "Incorrect username or password"


class SessionExpired(APIErrorModel):
    error_code: str = "USER_102"
    error_description: str = "User session expired, login again"
