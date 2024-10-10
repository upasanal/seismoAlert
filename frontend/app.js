async function getEarthquakeAlerts() {
    try {
        const response = await fetch('/earthquake-alerts'); // Calls the API endpoint
        const data = await response.json(); // Convert response to JSON
        document.getElementById('alerts').textContent = JSON.stringify(data, null, 2); // Display data
    } catch (error) {
        document.getElementById('alerts').textContent = 'Error fetching earthquake alerts.';
        console.error('Error:', error);
    }
}

async function sendMessage() {
    const chatBox = document.getElementById('chat-box');
    const message = document.getElementById('chat-message').value;
    if (message.trim() !== "") {
        const newMessage = document.createElement('div');
        newMessage.classList.add('chat-message', 'other-message');
        newMessage.innerHTML = `<strong>You:</strong> ${message}`;
        chatBox.appendChild(newMessage);
        document.getElementById('chat-message').value = "";
        chatBox.scrollTop = chatBox.scrollHeight;
    }
}

// Fetch earthquake alerts when the page loads
window.onload = getEarthquakeAlerts;

