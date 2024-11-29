from sqlmodel import Session, select
from datetime import datetime, timezone
from typing import List
import requests
from backend.entities.entities import Earthquake, ChatMessage, User, SubscribedUser
from backend.models.earthquakeDetails import EarthquakeDetails
from backend.models.chatDetails  import ChatDetails
from backend.models.userDetails import UserDetails
from twilio.rest import Client

TWILIO_ACCOUNT_SID = "AC01cf62aea894f2ad931ac36ffc3b42e8"
TWILIO_AUTH_TOKEN = "0ed98028e6f36e47b436d23c32a41bab"
TWILIO_PHONE_NUMBER = "+17756373836"
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Create tables
def create_tables(engine):
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)

    
def create_earthquake(
    session: Session, magnitude: float, location: str, latitude: float, longitude: float, depth: float = 0.0
) -> Earthquake:
    """
    Manually create an earthquake record in the database.
    """
    new_earthquake = Earthquake(
        magnitude=magnitude,
        location=location,
        latitude=latitude,
        longitude=longitude,
        depth=depth,
        event_time=datetime.now(tz=timezone.utc).isoformat(),
        created_at=datetime.now(tz=timezone.utc).isoformat(),
    )
    session.add(new_earthquake)
    session.commit()
    session.refresh(new_earthquake)
    return new_earthquake

def get_earthquakes(session: Session) -> List[EarthquakeDetails]:
    earthquakes = session.exec(
        select(Earthquake).order_by(Earthquake.event_time.desc())
    ).all()
    return earthquakes

def delete_earthquake(session: Session, earthquake_id: int):
    earthquake = session.get(Earthquake, earthquake_id)
    if not earthquake:
        raise Exception("Earthquake not found")
    session.delete(earthquake)
    session.commit()
    
# === ChatMessage Operations ===
def create_chat(session: Session, chat_data: ChatDetails) -> ChatMessage:
    chat = ChatMessage(
        user_id=chat_data.user_id,
        anonymous_name=chat_data.anonymous_name,
        message=chat_data.message,
        created_at=datetime.now(tz=timezone.utc).isoformat(),
    )
    session.add(chat)
    session.commit()
    session.refresh(chat)
    return chat

def get_chats(session: Session, limit: int = 10) -> List[ChatDetails]:
    chats = session.exec(select(ChatMessage).order_by(ChatMessage.created_at.desc()).limit(limit)).all()
    return chats

def update_chat(session: Session, chat_id: int, updated_message: str):
    chat = session.get(ChatMessage, chat_id)
    if not chat:
        raise Exception("Chat message not found")
    chat.message = updated_message
    session.commit()
    session.refresh(chat)
    return chat

def delete_chat(session: Session, chat_id: int):
    chat = session.get(ChatMessage, chat_id)
    if not chat:
        raise Exception("Chat message not found")
    session.delete(chat)
    session.commit()

# === User Operations ===
def create_user(session: Session, user_data: UserDetails) -> User:
    user = User(
        google_id=user_data.google_id,
        email=user_data.email,
        name=user_data.name,
        profile_pic=user_data.profile_pic,
        created_at=datetime.now(tz=timezone.utc).isoformat(),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def get_user(session: Session, user_id: int) -> UserDetails:
    user = session.get(User, user_id)
    if not user:
        raise Exception("User not found")
    return user

def update_user(session: Session, user_id: int, updated_data: UserDetails) -> User:
    user = session.get(User, user_id)
    if not user:
        raise Exception("User not found")
    for key, value in updated_data.dict(exclude_unset=True).items():
        setattr(user, key, value)
    session.commit()
    session.refresh(user)
    return user

def delete_user(session: Session, user_id: int):
    user = session.get(User, user_id)
    if not user:
        raise Exception("User not found")
    session.delete(user)
    session.commit()

# === Twilio Operations ===
def add_subscriber(session: Session, phone_number: str) -> SubscribedUser:
    existing_user = session.exec(
        select(SubscribedUser).where(SubscribedUser.phone_number == phone_number)
    ).first()
    if existing_user:
        raise Exception("User already subscribed")
    
    new_subscriber = SubscribedUser(
        phone_number=phone_number,
        subscribed_at=datetime.now(tz=timezone.utc).isoformat()
    )
    session.add(new_subscriber)
    session.commit()
    session.refresh(new_subscriber)
    return new_subscriber

def send_sms(phone_number: str, message: str):
    try:
        twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
    except Exception as e:
        print(f"Failed to send SMS to {phone_number}: {e}")

def send_sms_to_subscribers(session: Session, message: str):
    subscribers = session.exec(select(SubscribedUser)).all()
    for subscriber in subscribers:
        send_sms(subscriber.phone_number, message)


def get_all_subscribers(session: Session) -> List[SubscribedUser]:
    try:
        # Execute the query to get all SubscribedUser records
        subscribers = session.exec(select(SubscribedUser)).all()
        return subscribers
    except Exception as e:
        print(f"Error fetching subscribers: {e}")
        return []
    
def delete_all_subscribers(session: Session) -> int:
    try:
        num_deleted = session.query(SubscribedUser).delete()
        session.commit()
        return num_deleted
    except Exception as e:
        print(f"Error deleting all subscribers: {e}")
        return 0