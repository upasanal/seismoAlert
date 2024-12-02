let map;
let radius = 10; 
let websocket; 
let earthquakeMarkers = [];
let lat, lon;
let currentUserId = 1; 
let reconnectInterval = 3000; 
let websocketUrl = `ws://127.0.0.1:8001/ws/alerts`;
let receivedAlerts = new Map();

function initMap(lat, lon) {
    if (!map) {
        console.log("Initializing map...");  // Debugging line
        map = L.map('map').setView([lat, lon], getZoomLevel(radius)); 
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: 'Map data © <a href="https://openstreetmap.org">OpenStreetMap</a> contributors',
        }).addTo(map);
    } else {
        console.log("Updating map view...");  // Debugging line
        map.setView([lat, lon], getZoomLevel(radius)); 
    }

    const userMarker = L.marker([lat, lon], {
        icon: L.icon({
            iconUrl: 'https://maps.google.com/mapfiles/ms/icons/red-dot.png',
            iconSize: [32, 32],
            iconAnchor: [16, 32],
        }),
    }).addTo(map);

    userMarker.bindPopup(
        `<b>You are here</b><br>Latitude: ${lat.toFixed(6)}<br>Longitude: ${lon.toFixed(6)}`
    ).openPopup();

    fetchEarthquakeData(lat, lon, radius);
}

async function fetchEarthquakeData(latitude, longitude, radius) {
    try {
        const response = await fetch(`http://127.0.0.1:8000/earthquakes?lat=${latitude}&lon=${longitude}&radius=${radius}`);
        const earthquakeData = await response.json();

        console.log("Fetched Earthquake Data:", earthquakeData);  // Debugging line

        clearEarthquakeMarkers();

        earthquakeData.forEach((quake) => {
            addEarthquakeMarker(quake);
        });
    } catch (error) {
        console.error('Error fetching earthquake data:', error);
    }
}

// "See All" earthquakes - show all earthquakes on the map
async function seeAllEarthquakes() {
    try {
        const response = await fetch('http://127.0.0.1:8000/earthquakes/');
        const earthquakeData = await response.json();

        // Clear existing earthquake markers from the map
        clearEarthquakeMarkers();

        // Set zoom level to show the whole world
        map.setView([0, 0], 2);

        earthquakeData.forEach((quake) => {
            addEarthquakeMarker(quake);
        });
    } catch (error) {
        console.error('Error fetching all earthquakes:', error);
    }
}

function addEarthquakeMarker(quake) {
    let markerColor;
    if (quake.magnitude < 4) {
        markerColor = 'yellow';
    } else if (quake.magnitude < 5) {
        markerColor = 'orange';
    } else {
        markerColor = 'red';
    }

    const earthquakeIcon = L.circleMarker([quake.latitude, quake.longitude], {
        color: markerColor,
        radius: quake.magnitude * 5, 
        fillOpacity: 0.7
    });

    earthquakeIcon.bindPopup(`
        <b>Magnitude:</b> ${quake.magnitude}<br>
        <b>Location:</b> ${quake.location}<br>
        <b>Depth:</b> ${quake.depth} km<br>
        <b>Time:</b> ${new Date(quake.event_time).toLocaleString()}
    `);

    earthquakeIcon.addTo(map);
    earthquakeMarkers.push(earthquakeIcon);
}

function clearEarthquakeMarkers() {
    earthquakeMarkers.forEach(marker => {
        map.removeLayer(marker);
    });
    earthquakeMarkers = [];
}

function updateRadius() {
    radius = document.getElementById("radius-slider").value;
    document.getElementById("radius-value").innerText = radius;
    map.setView([lat, lon], getZoomLevel(radius));
    fetchEarthquakeData(lat, lon, radius);
    loadChatMessages();
    receivedAlerts.forEach((alertData, alertKey) => displayAlertMessage(alertKey, alertData));
}

function getZoomLevel(radius) {
    if (radius <= 5) return 12;
    if (radius <= 10) return 11;
    if (radius <= 20) return 10;
    if (radius <= 30) return 9;
    if (radius <= 50) return 8;
    if (radius <= 100) return 7;
    if (radius <= 500) return 6;
    if (radius <= 1000) return 5;
    if (radius <= 1500) return 4;
    if (radius <= 2000) return 3;
    return 2; 
}

//how websocket connection works
function connectWebSocket() {
    if (websocket) {
        websocket.close(); 
    }

    websocket = new WebSocket(websocketUrl);

    websocket.onopen = () => {
        console.log("Connected to WebSocket server for earthquake alerts");
        setInterval(() => {
            if (websocket.readyState === WebSocket.OPEN) {
                websocket.send(JSON.stringify({ type: "ping" }));
            }
        }, 25000); 
    };

    websocket.onmessage = (event) => {
        console.log("Message received:", event.data);
        const messageData = JSON.parse(event.data);
        if (messageData.type === "alert") {
            const alertKey = `${messageData.coordinates[0]}_${messageData.coordinates[1]}_${messageData.magnitude}`;
            if (!receivedAlerts.has(alertKey)) {
                receivedAlerts.set(alertKey, messageData); 
                displayAlertMessage(alertKey, messageData); 
            }
        } else if (messageData.type === "ping") {
            console.log("Ping received from server, WebSocket connection is active.");
        }
    };

    websocket.onclose = () => {
        console.log("WebSocket connection closed. Attempting to reconnect...");
        setTimeout(() => connectWebSocket(), reconnectInterval);
    };

    websocket.onerror = (error) => {
        console.error("WebSocket error:", error);
    };
}

function getColorByMagnitude(magnitude) {
    if (magnitude < 4) {
        return 'yellow';
    } else if (magnitude < 5) {
        return 'orange';
    } else {
        return 'red';
    }
}

async function loadChatMessages() {
    if (typeof lat === 'undefined' || typeof lon === 'undefined') {
        console.error("Latitude or Longitude is undefined. Cannot load chat messages.");
        return;
    }

    try {
        const url = `http://127.0.0.1:8000/chats/?user_lat=${lat}&user_lon=${lon}&radius=${radius}&limit=10`;
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        let chatMessages = await response.json();
        const chatBox = document.getElementById('chat-box');

        const noChatsMessage = chatBox.querySelector('.no-chats-message');
        if (noChatsMessage) {
            chatBox.removeChild(noChatsMessage);
        }

        Array.from(chatBox.children).forEach((child) => {
            if (!child.classList.contains('alert-message')) {
                chatBox.removeChild(child);
            }
        });

        if (!Array.isArray(chatMessages) || chatMessages.length === 0) {
            console.log("No nearby chats found.");
            if (!chatBox.querySelector('.no-chats-message')) {
                const noChatsMessage = document.createElement('p');
                noChatsMessage.textContent = "No chats found within this radius.";
                noChatsMessage.classList.add('no-chats-message'); 
                chatBox.appendChild(noChatsMessage);
            }
            return;
        }

        // Add chat messages to the chat box
        chatMessages.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
        chatMessages.forEach(chat => {
            displayChatMessage(chat);
        });
    } catch (error) {
        console.error('Error loading chat messages:', error);
    }
}


function displayChatMessage(chat, isCurrentUser = false) {
    const chatBox = document.getElementById('chat-box');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('chat-message');
    if (isCurrentUser || chat.user_id === currentUserId) {
        messageDiv.classList.add('user-message');
    } else {
        messageDiv.classList.add('other-message');
    }

    messageDiv.innerHTML = `<strong>${chat.anonymous_name || 'User'}:</strong> ${chat.message}`;
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
    const message = document.getElementById('chat-message').value;
    const displayName = document.getElementById('display-name').value.trim() || "Anonymous";

    if (!message.trim()) {
        alert("Please enter a message");
        return;
    }

    const chatData = {
        id: 0,
        user_id: currentUserId,
        anonymous_name: displayName,
        message: message,
        created_at: new Date().toISOString(),
        latitude: lat,
        longitude: lon
    };

    try {
        const response = await fetch('http://127.0.0.1:8000/chats/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(chatData)
        });

        if (response.ok) {
            const createdChat = await response.json();
            displayChatMessage(createdChat, true);
            document.getElementById('chat-message').value = '';
        } else {
            const errorData = await response.json();
            alert(`Error sending message: ${errorData.detail}`);
        }
    } catch (error) {
        console.error('Error sending message:', error);
    }
}

async function findNearbyShelters() {
    const latitude = document.getElementById('latitude').value;
    const longitude = document.getElementById('longitude').value;
    const radius = 16093; 
    const placeType = "shelter";
    const location = `${latitude},${longitude}`;

    const url = `http://127.0.0.1:8000/api/nearby-shelters?location=${location}&radius=${radius}&place_type=${placeType}`;

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error("Failed to fetch nearby shelters");
        }

        const data = await response.json();

        if (data.status === "OK") {
            displayShelters(data.results);
        } else {
            console.error("Error:", data.status, data.error_message);
            alert(`Failed to retrieve shelters: ${data.status}`);
        }
    } catch (error) {
        console.error("Error fetching data:", error);
        alert("Error fetching shelters.");
    }
}

function displayShelters(shelters) {
    const sheltersList = document.getElementById('shelters-list');
    sheltersList.innerHTML = '';

    shelters.forEach(shelter => {
        const shelterCard = document.createElement('div');
        shelterCard.classList.add('shelter-card');
        const shelterNameLink = document.createElement('a');
        shelterNameLink.href = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(shelter.name)}+${encodeURIComponent(shelter.vicinity)}`;
        shelterNameLink.target = "_blank";
        shelterNameLink.textContent = shelter.name;
        shelterNameLink.classList.add('shelter-link');

        const shelterName = document.createElement('h3');
        shelterName.appendChild(shelterNameLink);

        const shelterLocation = document.createElement('p');
        shelterLocation.innerHTML = `<strong>Location:</strong> ${shelter.vicinity}`;

        const shelterRating = document.createElement('p');
        shelterRating.innerHTML = `<strong>Rating:</strong> ${shelter.rating || 'N/A'} (${shelter.user_ratings_total || 0} reviews)`;

        shelterCard.appendChild(shelterName);
        shelterCard.appendChild(shelterLocation);
        shelterCard.appendChild(shelterRating);
        sheltersList.appendChild(shelterCard);
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const subscribeForm = document.getElementById("subscribe-form");
    if (subscribeForm) {
        subscribeForm.addEventListener("submit", function (event) {
            event.preventDefault(); 
            const phoneInput = document.getElementById("phone-number");
            if (!phoneInput) {
                console.error("Phone number input field not found.");
                return;
            }
            const phoneNumber = phoneInput.value;
            subscribeUser(phoneNumber); 
        });
    } else {
        console.log("Subscribe form not found on this page.");
    }
});

async function subscribeUser(phoneNumber) {
    const phoneRegex = /^\+\d{10,15}$/;
    if (!phoneNumber || !phoneRegex.test(phoneNumber.trim())) {
        alert("Please enter a valid phone number in the format specified.");
        return false;
    }
    if (websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({
            type: "subscribe",
            phone: phoneNumber.trim(),
        }));
        alert("Subscription request sent. Check your phone for confirmation.");
    } else {
        alert("WebSocket connection is not open. Please refresh the page and try again.");
    }
}

function displayAlertMessage(alertKey, alertData) {
    //https://www.movable-type.co.uk/scripts/latlong.html
    function calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 3958.8;
        const toRadians = (deg) => (deg * Math.PI) / 180;

        const dLat = toRadians(lat2 - lat1);
        const dLon = toRadians(lon2 - lon1);

        const a =
            Math.sin(dLat / 2) ** 2 +
            Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) *
            Math.sin(dLon / 2) ** 2;

        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c; 
    }

    try {
        const radiusSlider = document.getElementById("radius-slider");
        if (!radiusSlider) {
            console.error("Radius slider element not found.");
            return;
        }
        const radius = parseFloat(radiusSlider.value);

        if (typeof lat === "undefined" || typeof lon === "undefined") {
            console.error("User location (lat/lon) is undefined. Cannot calculate distance.");
            return;
        }

        const distance = calculateDistance(lat, lon, alertData.coordinates[0], alertData.coordinates[1]);

        const chatBox = document.getElementById("chat-box");
        if (!chatBox) {
            console.error("Chat box element not found.");
            return;
        }
        const existingAlert = Array.from(chatBox.children).find(
            (child) => child.dataset.alertKey === alertKey
        );

        if (distance <= radius) {
            if (!existingAlert) {
                const alertDiv = document.createElement("div");
                alertDiv.classList.add("alert-message");
                alertDiv.dataset.alertKey = alertKey;

                alertDiv.innerHTML = `
                    <strong>Earthquake Alert:</strong> 
                    Magnitude ${alertData.magnitude} at ${alertData.place}
                `;

                chatBox.appendChild(alertDiv);
                chatBox.scrollTop = chatBox.scrollHeight; 
                console.log(`Displayed alert: ${alertKey}`);
            }
        } else if (existingAlert) {
            chatBox.removeChild(existingAlert);
            console.log(`Removed alert: ${alertKey}`);
        }
    } catch (error) {
        console.error("Error in displayAlertMessage:", error);
    }
}



window.onload = function () {
    if (!websocket || websocket.readyState !== WebSocket.OPEN) {
        connectWebSocket();
    }
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function (position) {
            lat = position.coords.latitude;
            lon = position.coords.longitude;
            initMap(lat, lon);
            loadChatMessages(); 
        }, function (error) {
            console.error("Error getting location:", error);
            alert("Could not get your location. Please allow location access to use the live chat.");
        });
    } else {
        alert("Geolocation is not supported by your browser.");
    }
};
