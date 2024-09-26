from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ChatDetails(BaseModel):
    id: int
    user_id: Optional[int]
    anonymous_name: Optional[str]
    message: str
    created_at: datetime
    
    class Config:
        orm_mode = True  # Enable ORM mode for SQLAlchemy compatibility
