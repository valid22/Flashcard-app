from pydantic import BaseModel, validator
from typing import Union, Set

class CreateDeckRequest(BaseModel):
    name: str 
    tags: Union[str, Set[str]]

    @validator("tags")
    def validate_tags(cls, val):
        if isinstance(val, str):
            val = val.split(",")
        
        assert isinstance(val, list), "tags should be a list separated by comma"
        val = set(i.strip().lower() for i in val)

        assert len(val) < 5, "can assign a maximum of 4 tags to a deck"

        for tag in val:
            assert 1 <= len(tag) <= 12, "tag can be a maximum of 12 chars long"
        
        return val
    
    @validator("name")
    def validate_name(cls, val):
        assert isinstance(val, str), "name should be a valid string"
        assert 1 <= len(val) <= 120, "name can be a maximum of 120 chars long"

        return val

