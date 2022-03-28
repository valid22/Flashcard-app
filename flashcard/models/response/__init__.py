from typing import Any, Optional, List, Union
from pydantic import BaseModel
from flashcard.models.error import APIErrorModel

class APIResponse(BaseModel):
    success: bool 
    data: Union[Any, None]
    errors: Optional[List[Any]]
