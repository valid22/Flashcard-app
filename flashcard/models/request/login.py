from pydantic import BaseModel, validator
import hashlib

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