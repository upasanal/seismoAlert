from pydantic import BaseModel
from typing import Optional

class SubscriptionRequest(BaseModel):
    phone_number: str  # Input for subscription requests

class SubscriptionResponse(BaseModel):
    id: Optional[int]
    phone_number: str
    subscribed_at: Optional[str]
