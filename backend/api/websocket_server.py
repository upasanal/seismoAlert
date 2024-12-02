from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Query
from backend.api.service import *
from backend.api.main import get_session, engine
from sqlmodel import Session
import requests
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, List
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

last_connection_time = None

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler() 
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI()


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.fetch_task = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        if self.fetch_task is None or self.fetch_task.done():
            self.fetch_task = asyncio.create_task(fetch_earthquake_data())
            logging.info("Started earthquake data fetching task.")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        if not self.active_connections and self.fetch_task:
            self.fetch_task.cancel()
            logging.info("No active connections, stopping earthquake data fetching task.")

    async def broadcast(self, message: dict, session: Session):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
                logging.info(f"Sent message: {message}")  # Debug log to check if message is sent
            except Exception as e:
                logging.error(f"Failed to send message to a client: {e}")

manager = ConnectionManager()

async def fetch_earthquake_data():
    api_url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    start_time = "2024-11-30T00:00:00Z"
    params = {
        "starttime": start_time,
        "minmagnitude": 1.0,
        "format": "geojson"
    }

    while True:
        try:
            response = requests.get(api_url, params=params)
            data = response.json()
            if response.status_code != 200:
                logging.error(f"Failed to fetch data from USGS. Status Code: {response.status_code}, Response: {response.text}")
                await asyncio.sleep(60)
                continue

            with Session(engine) as session:
                for event in data.get("features", []):
                    try:
                        event_time = event.get("properties", {}).get("time")
                        if event_time is None:
                            logging.error(f"Missing 'time' key in event properties for event: {event}")
                            continue

                        magnitude = event["properties"]["mag"]
                        place = event["properties"]["place"]
                        coords = event["geometry"]["coordinates"]
                        epicenter = (coords[1], coords[0])
                        
                        event_time_utc = datetime.fromtimestamp(event_time / 1000, tz=timezone.utc)
                        new_earthquake = create_earthquake(
                            session,
                            magnitude=magnitude,
                            location=place,
                            latitude=epicenter[0],
                            longitude=epicenter[1],
                            event_time=event_time_utc,
                            depth=coords[2]  
                        )

                        logging.info(f"Added Earthquake to DB: Magnitude: {magnitude}, Location: {place}")

                        message = {
                            "type": "alert",
                            "magnitude": magnitude,
                            "place": place,
                            "coordinates": epicenter,
                            "depth": new_earthquake.depth,
                        }
                        await manager.broadcast(message, session)
                    except Exception as e:
                        logging.error(f"Error processing earthquake data: {e}")
            await asyncio.sleep(6000)

        except asyncio.CancelledError:
            logging.info("Earthquake fetching task has been cancelled.")
            break
        except Exception as e:
            logging.error(f"Error fetching earthquake data: {e}")
            await asyncio.sleep(60)

@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    global last_connection_time
    await manager.connect(websocket)
    session = next(get_session())
    last_connection_time = datetime.now(timezone.utc) 

    try:
        missed_alerts = get_missed_alerts(session)
        for alert in missed_alerts:
            await websocket.send_json(alert)
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=30)
            except asyncio.TimeoutError:
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

def get_last_connected_time():
    return last_connection_time

def get_missed_alerts(session: Session):
    """
    Fetch earthquakes from the database that occurred after the WebSocket server was last running.
    This should return alerts that were missed during any downtime.
    """
    missed_alerts = session.query(Earthquake).filter(Earthquake.event_time > get_last_connected_time()).all()
    alert_messages = []
    for earthquake in missed_alerts:
        alert_messages.append({
            "type": "alert",
            "magnitude": earthquake.magnitude,
            "place": earthquake.location,
            "coordinates": (earthquake.latitude, earthquake.longitude),
            "depth": earthquake.depth,
        })
    return alert_messages