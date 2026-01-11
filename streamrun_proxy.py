from flask import Flask, request, jsonify
import os
import requests
from datetime import datetime

app = Flask(__name__)

STREAMRUN_API_KEY = os.environ.get("STREAMRUN_API_KEY", "YOUR_API_KEY_HERE")
CONFIGURATION_ID = os.environ.get("STREAMRUN_CONFIGURATION_ID", "YOUR_CONFIGURATION_ID_HERE")

BASE_URL = "https://streamrun.com/api/v1"
HEADERS = {
    "Authorization": f"Bearer {STREAMRUN_API_KEY}",
    "Content-Type": "application/json"
}

# Store current instance ID in memory
current_instance = {
    "id": None,
    "started_at": None,
    "state": "UNKNOWN"
}


# ============ WEB DASHBOARD ============

@app.route("/")
def dashboard():
    """Serve the web control panel."""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Streamrun Control Panel</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            
            .container {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                padding: 30px;
                max-width: 500px;
                width: 100%;
            }
            
            .header {
                text-align: center;
                margin-bottom: 30px;
            }
            
            .header h1 {
                color: #333;
                font-size: 28px;
                margin-bottom: 10px;
            }
            
            .status-badge {
                display: inline-block;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 600;
                margin: 10px 0;
            }
            
            .status-running {
                background: #d4edda;
                color: #155724;
            }
            
            .status-stopped {
                background: #f8d7da;
                color: #721c24;
            }
            
            .status-unknown {
                background: #e2e3e5;
                color: #383d41;
            }
            
            .instance-info {
                background: #f8f9fa;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 25px;
                font-size: 13px;
                color: #666;
            }
            
            .instance-info strong {
                color: #333;
            }
            
            .button-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 12px;
                margin-bottom: 15px;
            }
            
            .button {
                padding: 14px 20px;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                text-align: center;
                text-decoration: none;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
            }
            
            .button:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
            }
            
            .button:active {
                transform: translateY(0);
            }
            
            .button-primary {
                background: #667eea;
                color: white;
                grid-column: 1 / -1;
            }
            
            .button-primary:hover {
                background: #5568d3;
            }
            
            .button-success {
                background: #28a745;
                color: white;
            }
            
            .button-success:hover {
                background: #218838;
            }
            
            .button-danger {
                background: #dc3545;
                color: white;
            }
            
            .button-danger:hover {
                background: #c82333;
            }
            
            .button-secondary {
                background: #6c757d;
                color: white;
            }
            
            .button-secondary:hover {
                background: #5a6268;
            }
            
            .button-full {
                grid-column: 1 / -1;
            }
            
            .input-group {
                margin-bottom: 15px;
            }
            
            .input-group label {
                display: block;
                margin-bottom: 8px;
                color: #333;
                font-weight: 600;
                font-size: 13px;
            }
            
            .input-group input,
            .input-group select {
                width: 100%;
                padding: 10px 12px;
                border: 1px solid #ddd;
                border-radius: 8px;
                font-size: 14px;
                font-family: inherit;
            }
            
            .input-group input:focus,
            .input-group select:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            .message {
                padding: 12px 15px;
                border-radius: 8px;
                margin-bottom: 15px;
                font-size: 13px;
                display: none;
            }
            
            .message.show {
                display: block;
            }
            
            .message-success {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            
            .message-error {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            
            .message-info {
                background: #d1ecf1;
                color: #0c5460;
                border: 1px solid #bee5eb;
            }
            
            .loading {
                display: none;
                text-align: center;
                color: #667eea;
                font-size: 13px;
            }
            
            .loading.show {
                display: block;
            }
            
            .spinner {
                display: inline-block;
                width: 12px;
                height: 12px;
                border: 2px solid #f3f3f3;
                border-top: 2px solid #667eea;
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .divider {
                height: 1px;
                background: #eee;
                margin: 20px 0;
            }
            
            @media (max-width: 600px) {
                .container {
                    padding: 20px;
                    border-radius: 15px;
                }
                
                .header h1 {
                    font-size: 24px;
                }
                
                .button {
                    padding: 12px 16px;
                    font-size: 13px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎬 Streamrun Control</h1>
                <div class="status-badge status-unknown" id="statusBadge">
                    Checking status...
                </div>
            </div>
            
            <div id="message" class="message"></div>
            <div class="loading" id="loading"><span class="spinner"></span> Loading...</div>
            
            <div class="instance-info">
                <strong>Instance:</strong> <span id="instanceId">None</span><br>
                <strong>State:</strong> <span id="instanceState">UNKNOWN</span><br>
                <strong>Started:</strong> <span id="instanceTime">—</span>
            </div>
            
            <div class="button-grid">
                <button class="button button-success" onclick="goLive()">
                    ▶ Go Live
                </button>
                <button class="button button-danger" onclick="stopInstance()">
                    ⏹ Stop
                </button>
            </div>
            
            <div class="button-grid">
                <button class="button button-secondary button-full" onclick="toggleLive()">
                    📡 Toggle Output (LIVE)
                </button>
                <button class="button button-secondary button-full" onclick="toggleOffline()">
                    📡 Toggle Output (OFFLINE)
                </button>
            </div>
            
            <div class="divider"></div>
            
            <div class="input-group">
                <label for="destId">Destination ID (for ingest switch)</label>
                <input type="text" id="destId" placeholder="Enter destination ID">
            </div>
            
            <button class="button button-secondary button-full" onclick="switchIngest()">
                🔄 Switch Ingest
            </button>
            
            <div class="divider"></div>
            
            <button class="button button-primary button-full" onclick="refreshStatus()">
                🔄 Refresh Status
            </button>
        </div>
        
        <script>
            const API_BASE = window.location.origin;
            
            function showMessage(text, type = 'info') {
                const msg = document.getElementById('message');
                msg.textContent = text;
                msg.className = `message show message-${type}`;
                setTimeout(() => msg.classList.remove('show'), 5000);
            }
            
            function setLoading(show) {
                document.getElementById('loading').classList.toggle('show', show);
            }
            
            function refreshInstanceData() {
                fetch(`${API_BASE}/api/instance-data`)
                    .then(r => r.json())
                    .then(data => {
                        document.getElementById('instanceId').textContent = data.id || 'None';
                        document.getElementById('instanceState').textContent = data.state || 'UNKNOWN';
                        document.getElementById('instanceTime').textContent = data.started_at || '—';
                        
                        const badge = document.getElementById('statusBadge');
                        badge.className = `status-badge status-${data.state.toLowerCase() || 'unknown'}`;
                        badge.textContent = data.state || 'UNKNOWN';
                    })
                    .catch(e => console.error('Error refreshing:', e));
            }
            
            function callAPI(endpoint, params = '') {
                setLoading(true);
                const url = `${API_BASE}${endpoint}${params}`;
                fetch(url)
                    .then(r => r.text())
                    .then(text => {
                        showMessage(text, 'success');
                        setLoading(false);
                        setTimeout(refreshInstanceData, 1000);
                    })
                    .catch(e => {
                        showMessage('Error: ' + e.message, 'error');
                        setLoading(false);
                    });
            }
            
            function goLive() {
                callAPI('/api/golive');
            }
            
            function stopInstance() {
                if (confirm('Stop stream instance?')) {
                    callAPI('/api/stop');
                }
            }
            
            function toggleLive() {
                callAPI('/api/outputs?state=LIVE');
            }
            
            function toggleOffline() {
                callAPI('/api/outputs?state=OFFLINE');
            }
            
            function switchIngest() {
                const destId = document.getElementById('destId').value.trim();
                if (!destId) {
                    showMessage('Please enter a destination ID', 'error');
                    return;
                }
                callAPI(`/api/switch?destination_id=${encodeURIComponent(destId)}`);
            }
            
            function refreshStatus() {
                refreshInstanceData();
                showMessage('Status refreshed', 'info');
            }
            
            // Load on startup
            refreshInstanceData();
        </script>
    </body>
    </html>
    """
    return html


@app.route("/api/instance-data")
def instance_data():
    """API endpoint for current instance data (JSON)."""
    return jsonify({
        "id": current_instance["id"] or "None",
        "state": current_instance["state"],
        "started_at": current_instance["started_at"] or "—"
    })


# ============ STREAMELEMENTS FRIENDLY API ============
# These endpoints return PLAIN TEXT only - perfect for $(customapi)

@app.route("/api/status")
def api_status():
    """Check instance status - returns plain text."""
    instance_id = current_instance["id"]
    
    if not instance_id:
        return "No active instance. Go live first."

    url = f"{BASE_URL}/instances/{instance_id}"
    r = requests.get(url, headers=HEADERS)
    if not r.ok:
        return f"Error {r.status_code}"

    data = r.json()
    state = data.get("state", "UNKNOWN")
    current_instance["state"] = state
    return state


@app.route("/api/golive")
def api_golive():
    """Start instance - returns plain text."""
    dest_id = request.args.get("destination_id", "")

    body = {
        "numberOfInstances": 1,
        "instanceSettings": [
            {
                "name": "Live Stream Instance",
                "overrides": {}
            }
        ]
    }

    if dest_id:
        body["instanceSettings"][0]["overrides"]["outputstream-1"] = {
            "destinations": [dest_id]
        }

    url = f"{BASE_URL}/configurations/{CONFIGURATION_ID}/instances"
    r = requests.post(url, headers=HEADERS, json=body)
    if not r.ok:
        return f"Error {r.status_code}"

    instances_url = f"{BASE_URL}/configurations/{CONFIGURATION_ID}/instances"
    instances_r = requests.get(instances_url, headers=HEADERS)
    
    if instances_r.ok:
        instances = instances_r.json()
        if instances:
            latest = instances[0]
            instance_id = latest.get("id")
            if instance_id:
                current_instance["id"] = instance_id
                current_instance["started_at"] = datetime.now().isoformat()
                current_instance["state"] = "QUEUED"
                return "Starting stream"

    return "Stream starting"


@app.route("/api/stop")
def api_stop():
    """Stop instance - returns plain text."""
    instance_id = current_instance["id"]
    
    if not instance_id:
        return "No active instance"
    
    url = f"{BASE_URL}/instances/{instance_id}"
    r = requests.delete(url, headers=HEADERS)
    if r.status_code in (200, 204):
        current_instance["id"] = None
        current_instance["state"] = "STOPPED"
        return "Stream stopped"
    return f"Error {r.status_code}"


@app.route("/api/outputs")
def api_outputs():
    """Toggle outputs - returns plain text."""
    state = request.args.get("state", "LIVE").upper()
    if state not in ("LIVE", "OFFLINE"):
        return "Invalid state"

    body = {"outputs": state}
    url = f"{BASE_URL}/configurations/{CONFIGURATION_ID}/instances"
    r = requests.put(url, headers=HEADERS, json=body)
    if not r.ok:
        return f"Error {r.status_code}"

    return f"Outputs {state}"


@app.route("/api/switch")
def api_switch():
    """Switch ingest - returns plain text."""
    dest_id = request.args.get("destination_id")
    if not dest_id:
        return "Missing destination_id"

    instance_id = current_instance["id"]
    
    if not instance_id:
        return "No active instance"

    body = {
        "outputstream-1": {
            "destinations": [dest_id]
        }
    }
    url = f"{BASE_URL}/instances/{instance_id}/overrides"
    r = requests.patch(url, headers=HEADERS, json=body)
    if not r.ok:
        return f"Error {r.status_code}"

    return "Ingest switched"


@app.route("/api/destinations")
def api_destinations():
    """List destinations - returns plain text."""
    url = f"{BASE_URL}/destinations"
    r = requests.get(url, headers=HEADERS)
    if not r.ok:
        return f"Error {r.status_code}"

    try:
        data = r.json()
        lines = []
        for d in data:
            name = d.get("name", "unknown")
            dest_id = d.get("id", "no-id")
            lines.append(f"{name}:{dest_id}")
        return " | ".join(lines) or "No destinations"
    except Exception:
        return "Error parsing"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
