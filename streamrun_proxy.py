from flask import Flask, request, jsonify
import os
import requests
from datetime import datetime
import json

app = Flask(__name__)

STREAMRUN_API_KEY = os.environ.get("STREAMRUN_API_KEY", "Qcd3vB4x85XSTuw683O9CaYXC6DU17sgDjamzmrgxks")
CONFIGURATION_ID = os.environ.get("STREAMRUN_CONFIGURATION_ID", "cmk8ofbmy005npb01zxi6yzec")

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

# Cache elements with categories
elements_cache = {
    "PC": None,
    "Mobile": None,
    "BRB Screen": None
}

# Store the switch element ID (found from config)
switch_element_id = None


def fetch_and_categorize_elements():
    """Fetch elements from configuration and categorize them."""
    global switch_element_id
    try:
        url = f"{BASE_URL}/configurations/{CONFIGURATION_ID}"
        r = requests.get(url, headers=HEADERS)
        if not r.ok:
            print(f"Error fetching config: {r.status_code}")
            return False
        
        data = r.json()
        config = data.get("configuration", {})
        elements = config.get("elements", [])
        
        # Reset categories
        elements_cache["PC"] = None
        elements_cache["Mobile"] = None
        elements_cache["BRB Screen"] = None
        
        # Map elements by title and find switch element
        for element in elements:
            elem_id = element.get("id", "")
            elem_title = element.get("title", "")
            elem_type = element.get("type", "")
            
            # Find the switch element
            if elem_type == "switch" or "switch" in elem_id.lower():
                switch_element_id = elem_id
                print(f"Found switch element: {elem_id}")
            
            # Match by title
            title_lower = elem_title.lower()
            
            if "pc" in title_lower and "screen" not in title_lower and "mobile" not in title_lower:
                elements_cache["PC"] = {"name": elem_title, "id": elem_id, "type": elem_type}
            elif "mobile" in title_lower:
                elements_cache["Mobile"] = {"name": elem_title, "id": elem_id, "type": elem_type}
            elif "brb" in title_lower or "be right back" in title_lower or "break" in title_lower:
                elements_cache["BRB Screen"] = {"name": elem_title, "id": elem_id, "type": elem_type}
        
        print(f"Elements loaded: PC={elements_cache['PC']}, Mobile={elements_cache['Mobile']}, BRB Screen={elements_cache['BRB Screen']}")
        print(f"Switch element ID: {switch_element_id}")
        return True
    except Exception as e:
        print(f"Error fetching elements: {e}")
        return False


# Fetch elements on startup
fetch_and_categorize_elements()


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
                background: #2a2a2a;
                color: #fff;
                min-height: 100vh;
                padding: 20px;
            }
            
            .dashboard {
                max-width: 1200px;
                margin: 0 auto;
            }
            
            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 30px;
            }
            
            .header h1 {
                font-size: 24px;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
                margin-bottom: 20px;
            }
            
            .panel {
                background: #3a3a3a;
                border-radius: 8px;
                padding: 20px;
                border: 1px solid #4a4a4a;
            }
            
            .panel-title {
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .panel-title .status-badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 600;
                margin-left: auto;
            }
            
            .status-badge.online {
                background: #28a745;
                color: white;
            }
            
            .status-badge.offline {
                background: #dc3545;
                color: white;
            }
            
            .status-badge.unknown {
                background: #6c757d;
                color: white;
            }
            
            .btn-group {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
                margin-bottom: 15px;
            }
            
            .btn-group.full {
                grid-template-columns: 1fr;
            }
            
            .btn {
                padding: 12px 16px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                text-align: center;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 6px;
            }
            
            .btn:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            }
            
            .btn:active {
                transform: translateY(0);
            }
            
            .btn-primary {
                background: #667eea;
                color: white;
            }
            
            .btn-primary:hover {
                background: #5568d3;
            }
            
            .btn-success {
                background: #28a745;
                color: white;
            }
            
            .btn-success:hover {
                background: #218838;
            }
            
            .btn-danger {
                background: #dc3545;
                color: white;
            }
            
            .btn-danger:hover {
                background: #c82333;
            }
            
            .btn-info {
                background: #17a2b8;
                color: white;
            }
            
            .btn-info:hover {
                background: #138496;
            }
            
            .btn-secondary {
                background: #6c757d;
                color: white;
            }
            
            .btn-secondary:hover {
                background: #5a6268;
            }
            
            .btn-element {
                background: #667eea;
                color: white;
                padding: 14px 12px;
                flex-direction: column;
                font-size: 13px;
            }
            
            .btn-element:hover {
                background: #5568d3;
            }
            
            .btn-element.active {
                background: #28a745;
                box-shadow: 0 0 10px rgba(40, 167, 69, 0.4);
            }
            
            .element-name {
                font-size: 11px;
                margin-top: 4px;
                opacity: 0.9;
            }
            
            .message {
                padding: 12px 16px;
                border-radius: 6px;
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
                padding: 10px;
            }
            
            .loading.show {
                display: block;
            }
            
            .spinner {
                display: inline-block;
                width: 12px;
                height: 12px;
                border: 2px solid #4a4a4a;
                border-top: 2px solid #667eea;
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
                margin-right: 6px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .info-block {
                background: #2a2a2a;
                border-radius: 6px;
                padding: 12px;
                font-size: 13px;
                margin-bottom: 10px;
            }
            
            .info-row {
                display: flex;
                justify-content: space-between;
                padding: 6px 0;
            }
            
            .info-row strong {
                color: #aaa;
            }
            
            .info-row span {
                color: #fff;
                font-weight: 600;
            }
            
            .full-width {
                grid-column: 1 / -1;
            }
            
            @media (max-width: 1024px) {
                .grid {
                    grid-template-columns: repeat(2, 1fr);
                }
            }
            
            @media (max-width: 768px) {
                .grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="dashboard">
            <div class="header">
                <h1>🎬 Streamrun Control Panel</h1>
                <div id="message" class="message"></div>
            </div>
            
            <div id="loading" class="loading"><span class="spinner"></span> Loading...</div>
            
            <div class="grid">
                <!-- Stream Control Panel -->
                <div class="panel">
                    <div class="panel-title">
                        Stream
                        <span class="status-badge offline" id="streamStatus">Offline</span>
                    </div>
                    <div class="btn-group full">
                        <button class="btn btn-success" onclick="goLive()">▶ Start</button>
                        <button class="btn btn-danger" onclick="stopInstance()">⏹ Stop</button>
                    </div>
                    <div class="info-block">
                        <div class="info-row">
                            <strong>Instance:</strong>
                            <span id="instanceId">None</span>
                        </div>
                        <div class="info-row">
                            <strong>State:</strong>
                            <span id="instanceState">UNKNOWN</span>
                        </div>
                        <div class="info-row">
                            <strong>Started:</strong>
                            <span id="instanceTime">—</span>
                        </div>
                    </div>
                </div>
                
                <!-- Element Selection Panel -->
                <div class="panel">
                    <div class="panel-title">
                        Element
                        <span class="status-badge offline">Select</span>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px;" id="elementButtons">
                        <!-- Buttons will be inserted here by JavaScript -->
                    </div>
                </div>
                
                <!-- Scene / Output Selection Panel -->
                <div class="panel">
                    <div class="panel-title">
                        Scene
                        <span class="status-badge online">Active</span>
                    </div>
                    <div class="btn-group full">
                        <button class="btn btn-primary" onclick="toggleLive()">📡 LIVE</button>
                        <button class="btn btn-secondary" onclick="toggleOffline()">📡 OFFLINE</button>
                    </div>
                </div>
            </div>
            
            <!-- Bottom action buttons -->
            <div class="grid full-width" style="grid-template-columns: 1fr;">
                <button class="btn btn-info" onclick="refreshStatus()">🔄 Refresh Status</button>
            </div>
        </div>
        
        <script>
            const API_BASE = window.location.origin;
            let currentElement = null;
            
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
                        
                        const statusBadge = document.getElementById('streamStatus');
                        const state = (data.state || 'UNKNOWN').toLowerCase();
                        statusBadge.className = `status-badge ${state === 'running' || state === 'queued' ? 'online' : 'offline'}`;
                        statusBadge.textContent = data.state || 'UNKNOWN';
                    })
                    .catch(e => console.error('Error refreshing:', e));
            }
            
            function loadElements() {
                fetch(`${API_BASE}/api/elements-categorized`)
                    .then(r => r.json())
                    .then(data => {
                        const container = document.getElementById('elementButtons');
                        container.innerHTML = '';
                        
                        const categories = ['PC', 'Mobile', 'BRB Screen'];
                        categories.forEach(cat => {
                            if (data[cat] && data[cat].id) {
                                const btn = document.createElement('button');
                                btn.className = 'btn btn-element';
                                btn.setAttribute('data-element-id', data[cat].id);
                                btn.innerHTML = `📺 ${cat}<span class="element-name">${data[cat].name}</span>`;
                                btn.onclick = () => switchElementTo(data[cat].id, btn);
                                container.appendChild(btn);
                            }
                        });
                    })
                    .catch(e => console.error('Error loading elements:', e));
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
            
            function switchElementTo(elementId, btnElement) {
                setLoading(true);
                const url = `${API_BASE}/api/switch-element?element_id=${encodeURIComponent(elementId)}`;
                fetch(url)
                    .then(r => r.text())
                    .then(text => {
                        showMessage(text, 'success');
                        
                        // Update active button styling
                        document.querySelectorAll('#elementButtons .btn-element').forEach(btn => {
                            btn.classList.remove('active');
                        });
                        if (btnElement) {
                            btnElement.classList.add('active');
                        }
                        
                        currentElement = elementId;
                        setLoading(false);
                    })
                    .catch(e => {
                        showMessage('Error: ' + e.message, 'error');
                        setLoading(false);
                    });
            }
            
            function refreshStatus() {
                refreshInstanceData();
                loadElements();
                showMessage('Status refreshed', 'info');
            }
            
            // Load on startup
            refreshInstanceData();
            loadElements();
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


@app.route("/api/elements-categorized")
def get_elements_categorized():
    """Get categorized elements (PC, Mobile, BRB Screen)."""
    return jsonify({
        "PC": elements_cache["PC"],
        "Mobile": elements_cache["Mobile"],
        "BRB Screen": elements_cache["BRB Screen"]
    })


# ============ STREAMELEMENTS FRIENDLY API ============
# These endpoints return PLAIN TEXT only - perfect for $(customapi)

@app.route("/api/status")
def api_status():
    """Check instance status - returns plain text."""
    try:
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
    except Exception as e:
        print(f"Error in api_status: {e}")
        return f"Error: {str(e)}"


@app.route("/api/golive")
def api_golive():
    """Start instance - returns plain text. Detects if already running by 0 slots error."""
    try:
        body = {
            "numberOfInstances": 1,
            "instanceSettings": [
                {
                    "name": "Live Stream Instance",
                    "overrides": {}
                }
            ]
        }

        url = f"{BASE_URL}/configurations/{CONFIGURATION_ID}/instances"
        print(f"POST {url} with body: {body}")
        r = requests.post(url, headers=HEADERS, json=body)
        
        # Check if instance is already running (0 slots available)
        if r.status_code == 400:
            error_text = r.text.lower()
            if "0 instance slots" in error_text or "no available slots" in error_text:
                print("Instance already running (no slots available)")
                # Get existing instance
                instances_url = f"{BASE_URL}/configurations/{CONFIGURATION_ID}/instances"
                instances_r = requests.get(instances_url, headers=HEADERS)
                
                if instances_r.ok:
                    instances_data = instances_r.json()
                    instances = instances_data.get("instances", [])
                    if instances:
                        for inst in instances:
                            state = inst.get("state", "").upper()
                            if state in ("RUNNING", "QUEUED", "STARTING"):
                                instance_id = inst.get("id")
                                if instance_id:
                                    current_instance["id"] = instance_id
                                    current_instance["state"] = state
                                    created_at = inst.get("createdAt") or inst.get("created_at")
                                    current_instance["started_at"] = created_at
                                    return f"Instance already running: {state}"
                
                return "Instance already running"
            else:
                return f"Error: {r.text}"
        
        if not r.ok:
            error_text = r.text
            print(f"Error {r.status_code}: {error_text}")
            return f"Error {r.status_code}: {error_text}"

        # Successfully created new instance
        instances_url = f"{BASE_URL}/configurations/{CONFIGURATION_ID}/instances"
        instances_r = requests.get(instances_url, headers=HEADERS)
        
        if instances_r.ok:
            instances_data = instances_r.json()
            instances = instances_data.get("instances", [])
            if instances:
                latest = instances[0]
                instance_id = latest.get("id")
                if instance_id:
                    current_instance["id"] = instance_id
                    current_instance["started_at"] = datetime.now().isoformat()
                    current_instance["state"] = "RUNNING"
                    return "Starting stream"

        return "Stream starting"
    except Exception as e:
        print(f"Error in api_golive: {e}")
        return f"Error: {str(e)}"


@app.route("/api/stop")
def api_stop():
    """Stop instance - returns plain text."""
    try:
        instance_id = current_instance["id"]
        
        if not instance_id:
            return "No active instance"
        
        url = f"{BASE_URL}/instances/{instance_id}"
        r = requests.delete(url, headers=HEADERS)
        if r.status_code in (200, 204):
            current_instance["id"] = None
            current_instance["state"] = "STOPPED"
            return "Stream stopped"
        return f"Error {r.status_code}: {r.text}"
    except Exception as e:
        print(f"Error in api_stop: {e}")
        return f"Error: {str(e)}"


@app.route("/api/outputs")
def api_outputs():
    """Toggle outputs LIVE/OFFLINE - returns plain text."""
    try:
        state = request.args.get("state", "LIVE").upper()
        if state not in ("LIVE", "OFFLINE"):
            return "Invalid state"

        instance_id = current_instance["id"]
        if not instance_id:
            return "No active instance. Start stream first."

        # Use PUT endpoint as per API docs for setting outputs
        url = f"{BASE_URL}/configurations/{CONFIGURATION_ID}/instances"
        body = {
            "outputs": state
        }
        print(f"PUT {url} with body: {body}")
        r = requests.put(url, headers=HEADERS, json=body)
        
        if not r.ok:
            print(f"Error {r.status_code}: {r.text}")
            return f"Error {r.status_code}: {r.text}"

        return f"Outputs {state}"
    except Exception as e:
        print(f"Error in api_outputs: {e}")
        return f"Error: {str(e)}"


@app.route("/api/switch-element")
def api_switch_element():
    """Switch element input - returns plain text. Uses PATCH /instances/{id}/overrides"""
    try:
        element_id = request.args.get("element_id")
        if not element_id:
            return "Missing element_id"

        instance_id = current_instance["id"]
        
        if not instance_id:
            return "No active instance. Start stream first."

        if not switch_element_id:
            return "Switch element not found in configuration"

        # PATCH the switch element with the selected input
        # Based on API docs: {"switch-1": {"input": "element-id"}}
        body = {
            switch_element_id: {
                "input": element_id
            }
        }
        
        url = f"{BASE_URL}/instances/{instance_id}/overrides"
        print(f"PATCH {url} with body: {body}")
        r = requests.patch(url, headers=HEADERS, json=body)
        
        if not r.ok:
            print(f"Error {r.status_code}: {r.text}")
            return f"Error {r.status_code}: {r.text}"

        print(f"Successfully switched to element {element_id}")
        return f"Switched to element"
    except Exception as e:
        print(f"Error in api_switch_element: {e}")
        return f"Error: {str(e)}"


@app.route("/api/destinations")
def api_destinations():
    """List destinations - returns plain text."""
    try:
        url = f"{BASE_URL}/destinations"
        r = requests.get(url, headers=HEADERS)
        if not r.ok:
            return f"Error {r.status_code}"

        data = r.json()
        lines = []
        for d in data:
            name = d.get("name", "unknown")
            dest_id = d.get("id", "no-id")
            lines.append(f"{name}:{dest_id}")
        return " | ".join(lines) or "No destinations"
    except Exception as e:
        print(f"Error in api_destinations: {e}")
        return f"Error: {str(e)}"


@app.errorhandler(500)
def handle_500(e):
    """Handle 500 errors gracefully."""
    print(f"500 Error: {e}")
    return f"Server Error: {str(e)}", 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)