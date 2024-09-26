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

// Fetch earthquake alerts when the page loads
window.onload = getEarthquakeAlerts;

