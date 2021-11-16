from os import error
from typing import List, Union, Optional
import json
from pydantic import BaseModel
from pydantic.dataclasses import dataclass
from pydantic.json import pydantic_encoder


class APIErrorModel(BaseModel):
    error_code: str
    error_description: str 
    status_code: Optional[int] = 500


class APIExceptionResponse(BaseModel):
    errors: List[APIErrorModel]
    status_code: Optional[int] = 500

    def __init__(self, errors, status_code):
        if isinstance(errors, APIErrorModel):
            errors = [errors]
        
        super().__init__(errors=errors, status_code=status_code)


class APIException(Exception):
    errors: APIExceptionResponse

    def __init__(self, e, status_code=500):
        self.errors = APIExceptionResponse(e, status_code=status_code)
    


