from os import error
from typing import List, Union
import json
from pydantic import BaseModel
from pydantic.dataclasses import dataclass
from pydantic.json import pydantic_encoder


class APIErrorModel(BaseModel):
    error_code: str
    error_description: str 
    status_code: int = 500


class APIExceptionResponse(BaseModel):
    errors: List[APIErrorModel]

    def __init__(self, errors):
        if not isinstance(errors, list):
            errors = [errors]
        
        super().__init__(errors=errors)


class APIException(Exception):
    errors: APIExceptionResponse

    def __init__(self, e):
        self.errors = APIExceptionResponse(e)
    


