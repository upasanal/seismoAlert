from sqlmodel import SQLModel, Field
from typing import Optional

# === Earthquake Entity ===
class Earthquake(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    magnitude: float
    location: str
    latitude: float
    longitude: float
    depth: float
    event_time: str  
    created_at: Optional[str] = None 

# === ChatMessage Entity ===
class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = None    # Can be nullable for anonymous users
    anonymous_name: Optional[str] = None  # Name for anonymous users
    message: str                     # Chat message content
    created_at: Optional[str] = None  # Message timestamp
    latitude: float
    longitude: float

# === User Entity ===
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    google_id: Optional[str] = None  # Google ID (nullable)
    email: str                       # User's email
    name: str                        # User's name
    profile_pic: Optional[str] = None # Optional profile picture
    created_at: Optional[str] = None  # Optional creation timestamp


# === Twilio Entity ===
class SubscribedUser(SQLModel, table=True):  # This creates the SubscribedUser table
    id: Optional[int] = Field(default=None, primary_key=True)
    phone_number: str = Field(index=True, unique=True)
    subscribed_at: str = Field(default=None)  # Optional timestamp for subscription