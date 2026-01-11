from flask import Flask, request, jsonify
import os
import requests
from datetime import datetime

app = Flask(__name__)

STREAMRUN_API_KEY = os.environ.get("STREAMRUN_API_KEY", "Qcd3vB4x85XSTuw683O9CaYXC6DU17sgDjamzmrgxks=")
CONFIGURATION_ID = os.environ.get("STREAMRUN_CONFIGURATION_ID", "cmk8ofbmy005npb01zxi6yzec")

BASE_URL = "https://streamrun.com/api/v1"
HEADERS = {
    "Authorization": f"Bearer {STREAMRUN_API_KEY}",
    "Content-Type": "application/json"
}

# Store current instance ID in memory
current_instance = {
    "id": None,
    "started_at": None
}


@app.route("/streamrun/status")
def stream_status():
    """Check instance status (for !bitrate / !status)."""
    instance_id = request.args.get("instance_id") or current_instance["id"]
    
    if not instance_id:
        return "Cloud server not active, wait for streamer to go live first.", 200
    
    url = f"{BASE_URL}/instances/{instance_id}"
    r = requests.get(url, headers=HEADERS)
    if not r.ok:
        return f"Error {r.status_code} checking status", 200

    data = r.json()
    state = data.get("state", "UNKNOWN")
    return f"Instance {instance_id} is {state}", 200


@app.route("/streamrun/golive", methods=["GET"])
def go_live():
    """
    Start a new instance from a configuration (for !golive).
    Optionally accept ?destination_id=... from SE.
    Stores the instance ID automatically.
    """
    dest_id = request.args.get("destination_id", "")

    body = {
        "numberOfInstances": 1,
        "instanceSettings": [
            {
                "name": "livestream",
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
        return f"Error {r.status_code} starting instance", 200

    # Extract instance request ID from Location header
    location = r.headers.get("Location", "")
    
    # Now fetch the actual instance from the configuration
    # This gets the latest instance (which we just started)
    instances_url = f"{BASE_URL}/configurations/{CONFIGURATION_ID}/instances"
    instances_r = requests.get(instances_url, headers=HEADERS)
    
    if instances_r.ok:
        instances = instances_r.json()
        if instances:
            latest = instances[0]  # Get first/latest instance
            instance_id = latest.get("id")
            if instance_id:
                current_instance["id"] = instance_id
                current_instance["started_at"] = datetime.now().isoformat()
                return f"Starting cloud server, please wait ~20 seconds...", 200

    return f"Starting stream (request: {location or 'unknown'}). Please run !status to confirm.", 200


@app.route("/streamrun/stop", methods=["GET"])
def stop_instance():
    """Stop a specific instance (for !offline)."""
    instance_id = request.args.get("instance_id") or current_instance["id"]
    
    if not instance_id:
        return "No active instance to stop.", 200
    
    url = f"{BASE_URL}/instances/{instance_id}"
    r = requests.delete(url, headers=HEADERS)
    if r.status_code in (200, 204):
        current_instance["id"] = None  # Clear stored instance
        return f"Stopping instance {instance_id}", 200
    return f"Error {r.status_code} stopping instance", 200


@app.route("/streamrun/outputs", methods=["GET"])
def toggle_outputs():
    """
    Set all outputs LIVE or OFFLINE for this configuration (for !live / !off).
    Example: /streamrun/outputs?state=LIVE or OFFLINE
    """
    state = request.args.get("state", "LIVE").upper()
    if state not in ("LIVE", "OFFLINE"):
        return "Invalid state, use LIVE or OFFLINE", 200

    body = {"outputs": state}
    url = f"{BASE_URL}/configurations/{CONFIGURATION_ID}/instances"
    r = requests.put(url, headers=HEADERS, json=body)
    if not r.ok:
        return f"Error {r.status_code} setting outputs {state}", 200

    return f"Outputs set to {state}", 200


@app.route("/streamrun/switch_ingest", methods=["GET"])
def switch_ingest():
    """
    Change destination for a running instance (for !switch).
    Example: /streamrun/switch_ingest?destination_id=DEST_ID
    """
    dest_id = request.args.get("destination_id")
    if not dest_id:
        return "Missing destination_id", 200

    instance_id = request.args.get("instance_id") or current_instance["id"]
    
    if not instance_id:
        return "No active instance. Run !golive first.", 200

    body = {
        "outputstream-1": {
            "destinations": [dest_id]
        }
    }
    url = f"{BASE_URL}/instances/{instance_id}/overrides"
    r = requests.patch(url, headers=HEADERS, json=body)
    if not r.ok:
        return f"Error {r.status_code} switching ingest", 200

    return f"Switched ingest to destination {dest_id}", 200


@app.route("/streamrun/current")
def get_current_instance():
    """Get currently stored instance ID and info."""
    if not current_instance["id"]:
        return "No active instance stored", 200
    
    return f"Current instance: {current_instance['id']} (started: {current_instance['started_at']})", 200


@app.route("/streamrun/set_instance", methods=["GET"])
def set_instance():
    """Manually set instance ID (useful if instance crashes and you start a new one)."""
    instance_id = request.args.get("instance_id")
    if not instance_id:
        return "Missing instance_id parameter", 200
    
    current_instance["id"] = instance_id
    current_instance["started_at"] = datetime.now().isoformat()
    return f"Set current instance to {instance_id}", 200


@app.route("/streamrun/destinations")
def list_destinations():
    """See configured destinations."""
    url = f"{BASE_URL}/destinations"
    r = requests.get(url, headers=HEADERS)
    if not r.ok:
        return f"Error {r.status_code} listing destinations", 200

    try:
        data = r.json()
    except Exception:
        return "Error parsing destinations", 200

    lines = []
    for d in data:
        name = d.get("name", "unknown")
        dest_id = d.get("id", "no-id")
        lines.append(f"{name}: {dest_id}")
    return " | ".join(lines) or "No destinations", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
