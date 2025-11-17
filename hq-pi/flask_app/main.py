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
    create_command,
    validate_message
)

# Import plugin system
from plugin_loader import PluginLoader
from context_store import ContextStore

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

# Initialize plugin system
plugin_loader = PluginLoader()
context_store = ContextStore()

# Load plugins at startup
logger.info("Loading plugins...")
loaded_plugins = plugin_loader.load_all_plugins()
logger.info(f"Loaded {len(loaded_plugins)} renderer plugins")


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


@app.route('/api/context/<device_id>')
def get_device_context(device_id):
    """Get all plugin context for a specific device"""
    context = context_store.get_device_context(device_id)
    return jsonify({
        "device_id": device_id,
        "context": context
    })


@app.route('/api/context/<device_id>/<plugin_id>')
def get_plugin_context(device_id, plugin_id):
    """Get specific plugin context for a device"""
    context = context_store.get_context(device_id, plugin_id)
    if context is None:
        return jsonify({"error": "Context not found"}), 404

    return jsonify({
        "device_id": device_id,
        "plugin_id": plugin_id,
        "context": context
    })


@app.route('/api/plugins')
def get_loaded_plugins():
    """Get list of loaded plugins"""
    plugins = []
    for plugin_id, plugin_info in loaded_plugins.items():
        manifest = plugin_info['manifest']
        plugins.append({
            "plugin_id": plugin_id,
            "name": manifest['name'],
            "version": manifest['version'],
            "author": manifest.get('author', 'Unknown')
        })

    return jsonify({
        "plugins": plugins,
        "count": len(plugins)
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

    # Send all stored plugin context to newly connected client
    send_all_plugin_context()


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


@socketio.on(MessageType.CONTEXT_UPDATE)
def handle_context_update(data):
    """
    Handle context update from collector plugin

    Expected data:
    {
        "type": "context_update",
        "device_id": "laptop-main",
        "plugin_id": "youtube",
        "data": {...},
        "timestamp": "..."
    }
    """
    device_id = data.get('device_id')
    plugin_id = data.get('plugin_id')
    context_data = data.get('data')
    timestamp = data.get('timestamp')

    if not all([device_id, plugin_id]):
        logger.warning(f"Invalid context update: missing required fields")
        return

    # If context_data is None or empty, plugin is inactive - remove from store
    if context_data is None or (isinstance(context_data, dict) and not context_data.get('active')):
        context_store.remove_plugin_context(device_id, plugin_id)
        logger.info(f"Plugin inactive, removed context: {device_id} / {plugin_id}")

        # Broadcast empty update to remove plugin from UI
        socketio.emit('plugin_update', {
            'device_id': device_id,
            'plugin_id': plugin_id,
            'widgets': [],
            'context': None,
            'timestamp': timestamp
        })
        return

    # Store context
    context_store.update_context(device_id, plugin_id, context_data, timestamp)
    logger.info(f"Received context update: {device_id} / {plugin_id}")

    # Render widgets for this plugin
    widgets = plugin_loader.render_plugin_widgets(plugin_id, context_data)

    if widgets is not None:
        # Broadcast plugin update to all connected UI clients
        socketio.emit('plugin_update', {
            'device_id': device_id,
            'plugin_id': plugin_id,
            'widgets': widgets,
            'context': context_data,
            'timestamp': timestamp
        })
        logger.debug(f"Broadcasted plugin update: {plugin_id}")


@socketio.on(MessageType.COMMAND_RESULT)
def handle_command_result(data):
    """
    Handle command result from collector

    Expected data:
    {
        "type": "command_result",
        "device_id": "laptop-main",
        "plugin_id": "youtube",
        "command_id": "...",
        "success": true,
        "message": "...",
        "request_id": "..."
    }
    """
    logger.info(f"Received command result: {data}")

    # Broadcast to UI clients
    socketio.emit('command_result', data)


@socketio.on('request_context')
def handle_request_context(data):
    """
    Handle request for immediate context update from UI

    Expected data:
    {
        "device_id": "laptop-main",
        "plugin_id": "youtube"  (optional)
    }
    """
    device_id = data.get('device_id')
    plugin_id = data.get('plugin_id')

    if not device_id:
        emit('error', create_error("device_id required"))
        return

    # Find collector session
    collector_session = None
    for sid, info in connected_collectors.items():
        if info['device_id'] == device_id:
            collector_session = sid
            break

    if not collector_session:
        emit('error', create_error(f"Collector not connected: {device_id}"))
        return

    # Request immediate context update from collector
    socketio.emit('request_context', {
        'plugin_id': plugin_id
    }, room=collector_session)

    logger.info(f"Requested context update from {device_id} for plugin: {plugin_id or 'all'}")


@socketio.on('send_command')
def handle_send_command(data):
    """
    Handle command from UI to be sent to collector

    Expected data:
    {
        "device_id": "laptop-main",
        "plugin_id": "youtube",
        "command_id": "pause",
        "args": {}
    }
    """
    device_id = data.get('device_id')
    plugin_id = data.get('plugin_id')
    command_id = data.get('command_id')
    args = data.get('args', {})

    if not all([device_id, plugin_id, command_id]):
        emit('error', create_error("Missing required fields"))
        return

    # Find collector session
    collector_session = None
    for sid, info in connected_collectors.items():
        if info['device_id'] == device_id:
            collector_session = sid
            break

    if not collector_session:
        emit('error', create_error(f"Collector not connected: {device_id}"))
        return

    # Send command to collector
    command_msg = create_command(device_id, plugin_id, command_id, args)
    command_msg['request_id'] = data.get('request_id')  # Pass through request ID if present

    socketio.emit(MessageType.COMMAND, command_msg, room=collector_session)
    logger.info(f"Sent command to {device_id}: {plugin_id}.{command_id}")


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


def send_all_plugin_context():
    """Send all stored plugin context to newly connected client"""
    all_context = context_store.get_all_context()

    for device_id, plugins in all_context.items():
        for plugin_id, stored_context in plugins.items():
            context_data = stored_context.get('data')
            timestamp = stored_context.get('timestamp')

            if context_data:
                # Render widgets for this plugin
                widgets = plugin_loader.render_plugin_widgets(plugin_id, context_data)

                if widgets is not None:
                    # Send plugin update to the newly connected client
                    emit('plugin_update', {
                        'device_id': device_id,
                        'plugin_id': plugin_id,
                        'widgets': widgets,
                        'context': context_data,
                        'timestamp': timestamp
                    })

    logger.debug(f"Sent all stored plugin context to new client")


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
