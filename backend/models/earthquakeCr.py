from pydantic import BaseModel

class EarthquakeCreate(BaseModel):
    magnitude: float
    location: str
    latitude: float
    longitude: float
    depth: float
    event_time: str
