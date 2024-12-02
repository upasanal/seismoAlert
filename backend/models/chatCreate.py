from pydantic import BaseModel
from typing import Optional

class ChatCreate(BaseModel):
    user_id: Optional[int]  # Either the user is logged in...
    anonymous_name: Optional[str]  # ...or they are anonymous
    latitude: float
    longitude: float
    message: str
    
    class Config:
        orm_mode = True  # Enable ORM mode for SQLAlchemy compatibility
