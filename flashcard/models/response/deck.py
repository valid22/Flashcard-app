from pydantic import BaseModel
from typing import List

class DeckResponseModel(BaseModel):
    deck_id: int
    deck_title: str 
    deck_tags: List[str]

