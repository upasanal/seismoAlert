from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import Session, create_engine
from typing import List, Optional
from backend.api.service import *
from backend.models.earthquakeDetails import EarthquakeDetails
from backend.models.chatDetails import ChatDetails
from backend.models.userDetails import UserDetails
from contextlib import asynccontextmanager
from backend.models.subscriptionDetails import SubscriptionRequest, SubscriptionResponse
from fastapi.middleware.cors import CORSMiddleware


DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session:
        yield session
        

@asynccontextmanager
async def lifespan(app: FastAPI):
    # This will be run when the app starts
    create_tables(engine)
    yield
    # This will be run when the app stops (cleanup logic can go here)

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with your frontend domain in production, e.g., ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (e.g., GET, POST, PUT, DELETE)
    allow_headers=["*"],  # Allow all headers
)

def get_session():
    with Session(engine) as session:
        yield session



@app.get("/earthquakes/", response_model=List[EarthquakeDetails], tags=["Earthquakes"])
def list_earthquakes(session: Session = Depends(get_session)):
    return get_earthquakes(session)

@app.delete("/earthquakes/{earthquake_id}", tags=["Earthquakes"])
def remove_earthquake(earthquake_id: int, session: Session = Depends(get_session)):
    try:
        delete_earthquake(session, earthquake_id)
        return {"message": f"Earthquake {earthquake_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    
@app.post("/earthquakes/", tags=["Earthquakes"])
def add_earthquake(
    magnitude: float,
    location: str,
    latitude: float,
    longitude: float,
    depth: Optional[float] = 0.0,
    session: Session = Depends(get_session)
):
    """
    Endpoint to manually create a new earthquake in the database for testing purposes.
    """
    try:
        # Call the service function to create an earthquake
        earthquake = create_earthquake(
            session=session,
            magnitude=magnitude,
            location=location,
            latitude=latitude,
            longitude=longitude,
            depth=depth
        )
        return {"message": "Earthquake created successfully", "earthquake": earthquake}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Chat Routes
@app.post("/chats/", response_model=ChatDetails, tags=["Chat"])
def post_chat(chat_data: ChatDetails, session: Session = Depends(get_session)):
    try:
        return create_chat(session, chat_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chats/", response_model=List[ChatDetails], tags=["Chat"])
def list_chats(limit: int = 10, session: Session = Depends(get_session)):
    return get_chats(session, limit)

@app.put("/chats/{chat_id}", response_model=ChatDetails, tags=["Chat"])
def edit_chat(chat_id: int, updated_message: str, session: Session = Depends(get_session)):
    try:
        return update_chat(session, chat_id, updated_message)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/chats/{chat_id}", tags=["Chat"])
def remove_chat(chat_id: int, session: Session = Depends(get_session)):
    try:
        delete_chat(session, chat_id)
        return {"message": f"Chat {chat_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# User Routes
@app.post("/users/", response_model=UserDetails, tags=["User"])
def post_user(user_data: UserDetails, session: Session = Depends(get_session)):
    try:
        return create_user(session, user_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}", response_model=UserDetails, tags=["User"])
def get_user_details(user_id: int, session: Session = Depends(get_session)):
    try:
        return get_user(session, user_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.put("/users/{user_id}", response_model=UserDetails, tags=["User"])
def edit_user(user_id: int, updated_data: UserDetails, session: Session = Depends(get_session)):
    try:
        return update_user(session, user_id, updated_data)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/users/{user_id}", tags=["User"])
def remove_user(user_id: int, session: Session = Depends(get_session)):
    try:
        delete_user(session, user_id)
        return {"message": f"User {user_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

from backend.models.subscriptionDetails import SubscriptionRequest, SubscriptionResponse

@app.post("/subscribe/", response_model=SubscriptionResponse, tags=["Subscriptions"])
def subscribe_user(request: SubscriptionRequest, session: Session = Depends(get_session)):
    try:
        new_subscriber = add_subscriber(session, request.phone_number)
        send_sms(request.phone_number, "Thank you for subscribing to SeismoAlert notifications!")
        return SubscriptionResponse(
            id=new_subscriber.id,
            phone_number=new_subscriber.phone_number,
            subscribed_at=new_subscriber.subscribed_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/subscribers/", response_model=List[SubscriptionResponse], tags=["Subscriptions"])
def list_subscribers(session: Session = Depends(get_session)):
    subscribers = get_all_subscribers(session)
    return [SubscriptionResponse(
        id=subscriber.id,
        phone_number=subscriber.phone_number,
        subscribed_at=subscriber.subscribed_at
    ) for subscriber in subscribers]

@app.delete("/subscribers/", response_model=dict, tags=["Subscriptions"])
def delete_all_subscribers_endpoint(session: Session = Depends(get_session)):
    num_deleted = delete_all_subscribers(session)
    if num_deleted > 0:
        return {"message": f"Successfully deleted {num_deleted} subscribers"}
    else:
        return {"message": "No subscribers to delete or an error occurred"}