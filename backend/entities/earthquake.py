from sqlmodel import SQLModel, Field
from typing import Optional

class Earthquake(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    magnitude: float
    location: str
    latitude: float
    longitude: float
    depth: float
    event_time: str  
    created_at: Optional[str] = None  