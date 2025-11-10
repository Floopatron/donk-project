"""
Donk HQ Pi Server - Main Flask Application

This is the central server that:
- Accepts WebSocket connections from collectors
- Accepts WebSocket connections from Donk clients
- Routes messages between components
- Serves the web UI
"""

import sys
import os
from pathlib import Path
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit, disconnect
from datetime import datetime, timezone
import logging

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))
from protocol import (
    MessageType,
    create_collector_list,
    create_error,
    validate_message
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app with correct paths
# Templates and static folders are in parent directory (hq-pi/)
base_dir = Path(__file__).parent.parent
app = Flask(
    __name__,
    template_folder=str(base_dir / 'templates'),
    static_folder=str(base_dir / 'static')
)
app.config['SECRET_KEY'] = 'donk-secret-key-change-in-production'  # TODO: Move to config file

# Initialize SocketIO with eventlet
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# In-memory storage for connected collectors
# Structure: {session_id: {device_id, hostname, platform, connected_at}}
connected_collectors = {}


# =============================================================================
# HTTP Routes
# =============================================================================

@app.route('/')
def index():
    """Serve main UI page"""
    return render_template('index.html')


@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "server": "Donk HQ Pi",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "collectors_connected": len(connected_collectors)
    })


@app.route('/api/collectors')
def get_collectors():
    """Get list of connected collectors"""
    collectors = [
        {
            "device_id": info["device_id"],
            "hostname": info["hostname"],
            "platform": info["platform"],
            "connected_at": info["connected_at"]
        }
        for info in connected_collectors.values()
    ]
    return jsonify({
        "collectors": collectors,
        "count": len(collectors)
    })


# =============================================================================
# WebSocket Event Handlers
# =============================================================================

@socketio.on('connect')
def handle_connect(auth=None):
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connection_established', {'status': 'connected'})

    # Send current collector list to newly connected client
    broadcast_collector_list()


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    from flask import request

    # Check if this was a collector
    if request.sid in connected_collectors:
        collector_info = connected_collectors[request.sid]
        logger.info(f"Collector disconnected: {collector_info['device_id']}")
        del connected_collectors[request.sid]

        # Broadcast updated collector list
        broadcast_collector_list()
    else:
        logger.info(f"Client disconnected: {request.sid}")


@socketio.on(MessageType.COLLECTOR_REGISTER)
def handle_collector_register(data):
    """
    Handle collector registration

    Expected data:
    {
        "type": "collector_register",
        "device_id": "laptop-main",
        "hostname": "my-laptop",
        "platform": "Linux"
    }
    """
    from flask import request

    if not validate_message(data):
        logger.warning(f"Invalid registration message from {request.sid}")
        emit('error', create_error("Invalid registration message"))
        return

    device_id = data.get('device_id')
    hostname = data.get('hostname')
    platform = data.get('platform')

    # Store collector info
    connected_collectors[request.sid] = {
        "device_id": device_id,
        "hostname": hostname,
        "platform": platform,
        "connected_at": datetime.now(timezone.utc).isoformat(),
        "session_id": request.sid
    }

    logger.info(f"Collector registered: {device_id} ({hostname}, {platform})")

    # Send acknowledgment
    emit('registration_ack', {
        "status": "registered",
        "device_id": device_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    # Broadcast updated collector list to all clients
    broadcast_collector_list()


@socketio.on(MessageType.COLLECTOR_HEARTBEAT)
def handle_collector_heartbeat(data):
    """
    Handle collector heartbeat

    Expected data:
    {
        "type": "collector_heartbeat",
        "device_id": "laptop-main"
    }
    """
    from flask import request

    device_id = data.get('device_id')

    # Update last heartbeat time
    if request.sid in connected_collectors:
        connected_collectors[request.sid]['last_heartbeat'] = datetime.now(timezone.utc).isoformat()
        logger.debug(f"Heartbeat from {device_id}")

        # Send lightweight heartbeat update to UI instead of full list
        socketio.emit('collector_heartbeat_update', {
            'device_id': device_id,
            'last_heartbeat': connected_collectors[request.sid]['last_heartbeat']
        })
    else:
        logger.warning(f"Heartbeat from unregistered collector: {device_id}")


@socketio.on(MessageType.PING)
def handle_ping(data):
    """Handle ping request"""
    emit(MessageType.PONG, {'timestamp': datetime.now(timezone.utc).isoformat()})


# =============================================================================
# Helper Functions
# =============================================================================

def broadcast_collector_list():
    """Broadcast updated collector list to all connected clients"""
    collectors = [
        {
            "device_id": info["device_id"],
            "hostname": info["hostname"],
            "platform": info["platform"],
            "connected_at": info["connected_at"],
            "last_heartbeat": info.get("last_heartbeat", info["connected_at"]),
            "session_id": info["session_id"]
        }
        for info in connected_collectors.values()
    ]

    message = create_collector_list(collectors)
    socketio.emit(MessageType.COLLECTOR_LIST, message)
    logger.debug(f"Broadcasted collector list: {len(collectors)} collectors")


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == '__main__':
    logger.info("="*60)
    logger.info("Donk HQ Pi Server Starting")
    logger.info("="*60)
    logger.info(f"Listening on: http://0.0.0.0:5000")
    logger.info(f"Tailscale IP: http://100.74.135.15:5000")
    logger.info(f"Press Ctrl+C to stop")
    logger.info("="*60)

    # Run server
    # host='0.0.0.0' makes it accessible from other devices
    # debug=False for production
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
