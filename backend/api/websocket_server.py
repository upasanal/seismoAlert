from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Query
from backend.api.service import *
from backend.api.main import get_session
from sqlmodel import Session
import requests
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, List
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict, session: Session):
        # Broadcast to active WebSocket connections
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logging.error(f"Failed to send message to a client: {e}")

        # Send SMS notifications to subscribers if it's an alert
        if message.get("type") == "alert":
            alert_message = f"Earthquake Alert! Magnitude: {message['magnitude']} at {message['place']}"
            send_sms_to_subscribers(session, alert_message)

manager = ConnectionManager()

async def fetch_earthquake_data():
    api_url = "https://earthquake.usgs.gov/fdsnws/event/1/query"

    # Fixed start time: Always fetch data from November 29th, 2024 onward
    start_time = "2024-11-29T00:00:00Z"
    params = {
        "starttime": start_time,
        "minmagnitude": 1.0,
        "format": "geojson"
    }

    while True:
        try:
            response = requests.get(api_url, params=params)
            data = response.json()

            # Add more detailed error handling
            if response.status_code != 200:
                logging.error(f"Failed to fetch data from USGS. Status Code: {response.status_code}, Response: {response.text}")
                await asyncio.sleep(60)
                continue

            with next(get_session()) as session:
                for event in data.get("features", []):
                    try:
                        magnitude = event["properties"]["mag"]
                        place = event["properties"]["place"]
                        coords = event["geometry"]["coordinates"]
                        epicenter = (coords[1], coords[0])

                        # Add earthquake to the database
                        new_earthquake = create_earthquake(
                            session,
                            magnitude=magnitude,
                            location=place,
                            latitude=epicenter[0],
                            longitude=epicenter[1],
                            depth=coords[2]  # Assuming depth is available as the third element
                        )

                        # Log successful earthquake creation
                        logging.info(f"Added Earthquake to DB: Magnitude: {magnitude}, Location: {place}")

                        # Broadcast new earthquake to all connected clients
                        message = {
                            "type": "alert",
                            "magnitude": magnitude,
                            "place": place,
                            "coordinates": epicenter,
                            "depth": new_earthquake.depth,
                            "event_time": new_earthquake.event_time
                        }
                        await manager.broadcast(message, session)
                    except Exception as e:
                        logging.error(f"Error processing earthquake data: {e}")

            # Fetch data every 60 seconds
            await asyncio.sleep(60)

        except Exception as e:
            logging.error(f"Error fetching earthquake data: {e}")
            await asyncio.sleep(60)

@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    session = next(get_session())

    try:
        while True:
            # Wait for data from client to handle subscriptions or pings
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=30)
            except asyncio.TimeoutError:
                # Keep-alive ping to avoid disconnection
                await websocket.send_json({"type": "ping"})
                continue

            if data.get("type") == "subscribe":
                phone_number = data.get("phone")
                if phone_number:
                    try:
                        add_subscriber(session, phone_number)
                        send_sms(
                            phone_number,
                            "You are now subscribed to SeismoAlert notifications!"
                        )
                    except Exception as e:
                        logging.error(f"Subscription error: {e}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logging.error(f"Unexpected error with WebSocket: {e}")
    finally:
        session.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions - start background task
    task = asyncio.create_task(fetch_earthquake_data())
    yield
    # Shutdown actions - cancel the background task
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        logging.info("Background earthquake fetching task has been cancelled.")

# Create the app with lifespan
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins, you can change this to specific domains.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)