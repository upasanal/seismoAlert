from sqlmodel import SQLModel, Field
from typing import Optional

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    google_id: Optional[str] = None  # Google ID (nullable)
    email: str                       # User's email
    name: str                        # User's name
    profile_pic: Optional[str] = None # Optional profile picture
    created_at: Optional[str] = None  # Optional creation timestamp
