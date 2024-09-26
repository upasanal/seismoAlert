from sqlmodel import SQLModel, Field
from typing import Optional

class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = None    # Can be nullable for anonymous users
    anonymous_name: Optional[str] = None  # Name for anonymous users
    message: str                     # Chat message content
    created_at: Optional[str] = None  # Message timestamp
