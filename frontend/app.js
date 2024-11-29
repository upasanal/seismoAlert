// Edited version of app.js
let map;
let radius = 10; // Default chat radius in miles
let websocket; // WebSocket connection for earthquake alerts
let earthquakeMarkers = [];
let lat, lon; // User's location
let currentUserId = 1; // Placeholder for current user ID
let reconnectInterval = 3000; // Interval for WebSocket reconnection in milliseconds
let websocketUrl = `ws://127.0.0.1:8001/ws/alerts`; // WebSocket URL for earthquake alerts

// Initialize the map
function initMap(lat, lon) {
    map = L.map('map').setView([lat, lon], getZoomLevel(radius)); // Set view using user's location and radius-based zoom level

    // Add tile layer to map
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: 'Map data © <a href="https://openstreetmap.org">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Add marker for user's location
    const userMarker = L.marker([lat, lon], {
        icon: L.icon({
            iconUrl: 'https://maps.google.com/mapfiles/ms/icons/red-dot.png',
            iconSize: [32, 32],
            iconAnchor: [16, 32],
        })
    }).addTo(map);
    userMarker.bindPopup('<b>You are here</b>').openPopup();

    // Fetch and plot earthquakes on the map
    fetchEarthquakeData(lat, lon, radius);
    connectWebSocket(); // Connect to WebSocket for live earthquake alerts
}

// Fetch earthquake data for the given latitude, longitude, and radius
async function fetchEarthquakeData(latitude, longitude, radius) {
    try {
        const response = await fetch(`http://127.0.0.1:8000/earthquakes?lat=${latitude}&lon=${longitude}&radius=${radius}`);
        const earthquakeData = await response.json();

        // Clear existing earthquake markers from the map
        clearEarthquakeMarkers();

        // Add new markers for the fetched earthquakes
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

        // Add markers for all earthquakes in the database
        earthquakeData.forEach((quake) => {
            addEarthquakeMarker(quake);
        });
    } catch (error) {
        console.error('Error fetching all earthquakes:', error);
    }
}

// Function to add a marker for an earthquake to the map
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
        radius: quake.magnitude * 5, // Adjust radius based on magnitude
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

// Clear all earthquake markers from the map
function clearEarthquakeMarkers() {
    earthquakeMarkers.forEach(marker => {
        map.removeLayer(marker);
    });
    earthquakeMarkers = [];
}

// Update radius and refresh earthquake markers
function updateRadius() {
    radius = document.getElementById("radius-slider").value;
    document.getElementById("radius-value").innerText = radius;

    // Recalculate map zoom level based on radius
    map.setView([lat, lon], getZoomLevel(radius));

    // Fetch earthquake data with updated radius
    fetchEarthquakeData(lat, lon, radius);
}

// Get zoom level based on the radius (approximate)
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
    return 2; // For larger radii
}

// Connect to WebSocket for real-time earthquake alerts
function connectWebSocket() {
    if (websocket) {
        websocket.close(); // Close any existing connection before opening a new one
    }

    websocket = new WebSocket(websocketUrl);

    websocket.onopen = () => {
        console.log("Connected to WebSocket server for earthquake alerts");
        setInterval(() => {
            if (websocket.readyState === WebSocket.OPEN) {
                websocket.send(JSON.stringify({ type: "ping" }));
            }
        }, 25000); // Keep-alive ping every 25 seconds
    };

    websocket.onmessage = (event) => {
        const messageData = JSON.parse(event.data);
        if (messageData.type === "alert") {
            plotEarthquake(messageData); // Plot the earthquake on the map
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

// Plot individual earthquake from WebSocket message
function plotEarthquake(earthquake) {
    const color = getColorByMagnitude(earthquake.magnitude);
    const marker = L.circle([earthquake.coordinates[0], earthquake.coordinates[1]], {
        radius: earthquake.magnitude * 100, // Scale radius based on magnitude
        color: color,
        fillColor: color,
        fillOpacity: 0.5
    }).addTo(map);

    marker.bindPopup(
        `<strong>Magnitude:</strong> ${earthquake.magnitude}<br>
         <strong>Location:</strong> ${earthquake.place}`
    );

    earthquakeMarkers.push(marker);
}

// Get color by earthquake magnitude
function getColorByMagnitude(magnitude) {
    if (magnitude < 4) {
        return 'yellow';
    } else if (magnitude < 5) {
        return 'orange';
    } else {
        return 'red';
    }
}

// Load chat messages from the server
async function loadChatMessages() {
    try {
        const response = await fetch('http://127.0.0.1:8000/chats/');
        let chatMessages = await response.json();

        // Sort messages by created_at
        chatMessages.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));

        // Clear the chat box before appending
        const chatBox = document.getElementById('chat-box');
        chatBox.innerHTML = '';

        // Display each message in order
        chatMessages.forEach(chat => {
            displayChatMessage(chat);
        });
    } catch (error) {
        console.error('Error loading chat messages:', error);
    }
}

// Display chat messages in the chat box
function displayChatMessage(chat, isCurrentUser = false) {
    const chatBox = document.getElementById('chat-box');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('chat-message');

    // Apply the appropriate CSS class based on the message sender
    if (isCurrentUser || chat.user_id === currentUserId) {
        messageDiv.classList.add('user-message');
    } else {
        messageDiv.classList.add('other-message');
    }

    messageDiv.innerHTML = `<strong>${chat.anonymous_name || 'User'}:</strong> ${chat.message}`;
    chatBox.appendChild(messageDiv);

    // Scroll to the bottom of the chat box to see the latest message
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Send chat message through HTTP POST
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
        created_at: new Date().toISOString()
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

// Window onload function to initialize map and chat
window.onload = function () {
    loadChatMessages(); // Load chat messages on page load
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function (position) {
            lat = position.coords.latitude;
            lon = position.coords.longitude;
            initMap(lat, lon);
        }, function (error) {
            console.error("Error getting location:", error);
            alert("Could not get your location. Please allow location access to use the live chat.");
        });
    } else {
        alert("Geolocation is not supported by your browser.");
    }
};
