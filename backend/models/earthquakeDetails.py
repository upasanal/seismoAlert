from pydantic import BaseModel
from typing import Optional

class EarthquakeDetails(BaseModel):
    id: Optional[int]
    magnitude: float
    location: str
    latitude: float
    longitude: float
    depth: float
    event_time: str
    created_at: Optional[str]

    class Config:
        orm_mode = True  # Enables ORM-to-Pydantic conversion
