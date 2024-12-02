from pydantic import BaseModel
from typing import Optional

class ChatCreate(BaseModel):
    user_id: Optional[int]  
    anonymous_name: Optional[str]  
    latitude: float
    longitude: float
    message: str
    
    class Config:
        orm_mode = True 
