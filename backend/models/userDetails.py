from pydantic import BaseModel
from typing import Optional

class UserDetails(BaseModel):
    id: Optional[int]
    google_id: Optional[str]
    email: str
    name: str
    profile_pic: Optional[str]
    
    class Config:
        orm_mode = True 