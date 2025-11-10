#!/usr/bin/env python3
"""
Donk Collector Agent

Runs on desktop/laptop devices to:
- Connect to HQ Pi via WebSocket
- Register with unique device ID
- Send heartbeats to maintain connection
- Auto-reconnect if connection drops

Usage:
    python collector.py [--hq-url ws://100.74.135.15:5000]
"""

import sys
import os
import socket
import platform
import time
import signal
import logging
import argparse
from pathlib import Path
from datetime import datetime

import socketio

# Add shared module to path
# Changes to run on laptop
ROOT = Path(__file__).resolve().parents[1]  # repo root: ...\donk-project\donk-project
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
    
from shared.protocol import (
    MessageType,
    create_collector_register,
    create_collector_heartbeat
)

# Configure logging
logging.getLogger().setLevel(logging.DEBUG)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# Global flag for graceful shutdown
shutdown_requested = False


class DonkCollector:
    """
    Donk Collector Agent

    Connects to HQ Pi and maintains connection with auto-reconnect logic.
    """

    def __init__(self, hq_url: str):
        """
        Initialize collector

        Args:
            hq_url: WebSocket URL of HQ Pi server (e.g., ws://100.74.135.15:5000)
        """
        self.hq_url = hq_url
        self.device_id = self._generate_device_id()
        self.hostname = socket.gethostname()
        self.platform = platform.system()

        # Create Socket.IO client
        self.sio = socketio.Client(
            reconnection=True,
            reconnection_attempts=0,  # Infinite retries
            reconnection_delay=1,      # Start with 1 second
            reconnection_delay_max=30, # Max 30 seconds between retries
            logger=False,
            engineio_logger=False
        )

        # Register event handlers
        self._register_handlers()

        # Heartbeat settings
        self.heartbeat_interval = 30  # seconds
        self.last_heartbeat = None

    def _generate_device_id(self) -> str:
        """
        Generate unique device ID based on hostname and platform

        Returns:
            Device ID string
        """
        hostname = socket.gethostname()
        # Clean hostname (remove special chars)
        clean_hostname = ''.join(c for c in hostname if c.isalnum() or c in ['-', '_'])
        return f"{clean_hostname}-{platform.system().lower()}"

    def _register_handlers(self):
        """Register Socket.IO event handlers"""

        @self.sio.on('connect')
        def on_connect():
            logger.info(f"Connected to HQ Pi: {self.hq_url}")
            # Send registration message
            self._send_registration()

        @self.sio.on('disconnect')
        def on_disconnect():
            logger.warning("Disconnected from HQ Pi")
            logger.info("Will attempt to reconnect...")

        @self.sio.on('registration_ack')
        def on_registration_ack(data):
            logger.info(f"Registration acknowledged by HQ Pi")
            logger.info(f"Device ID: {self.device_id}")
            logger.info(f"Status: {data.get('status')}")

        @self.sio.on('error')
        def on_error(data):
            logger.error(f"Error from HQ Pi: {data}")

        @self.sio.on('connection_established')
        def on_connection_established(data):
            logger.debug(f"Connection established: {data}")

    def _send_registration(self):
        """Send registration message to HQ Pi"""
        msg = create_collector_register(
            device_id=self.device_id,
            hostname=self.hostname,
            platform=self.platform
        )
        self.sio.emit(MessageType.COLLECTOR_REGISTER, msg)
        logger.debug(f"Sent registration: {self.device_id}")

    def _send_heartbeat(self):
        """Send heartbeat to HQ Pi"""
        if self.sio.connected:
            msg = create_collector_heartbeat(self.device_id)
            self.sio.emit(MessageType.COLLECTOR_HEARTBEAT, msg)
            self.last_heartbeat = datetime.utcnow()
            logger.debug(f"Sent heartbeat")

    def connect(self):
        """Connect to HQ Pi server"""
        logger.info("="*60)
        logger.info("Donk Collector Agent Starting")
        logger.info("="*60)
        logger.info(f"Device ID: {self.device_id}")
        logger.info(f"Hostname: {self.hostname}")
        logger.info(f"Platform: {self.platform}")
        logger.info(f"HQ Pi URL: {self.hq_url}")
        logger.info("="*60)

        try:
            logger.info("Connecting to HQ Pi...")
            self.sio.connect(self.hq_url, wait_timeout=10)
            logger.info("Connection established!")

        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            logger.info("Entering standby mode - will retry automatically...")
            # Socket.IO client will automatically retry connection
            # based on reconnection settings

    def run(self):
        """
        Main run loop

        Maintains connection and sends periodic heartbeats.
        """
        global shutdown_requested

        # Connect to HQ Pi
        self.connect()

        # Main loop
        try:
            logger.info("Collector agent running. Press Ctrl+C to stop.")

            while not shutdown_requested:
                # Send heartbeat if connected
                current_time = time.time()
                if self.last_heartbeat is None or \
                   (datetime.utcnow() - self.last_heartbeat).total_seconds() >= self.heartbeat_interval:
                    self._send_heartbeat()

                # Sleep briefly
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            shutdown_requested = True

        finally:
            self.shutdown()

    def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down collector...")

        if self.sio.connected:
            logger.info("Disconnecting from HQ Pi...")
            self.sio.disconnect()

        logger.info("Collector stopped")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global shutdown_requested
    logger.info(f"Received signal {signum}")
    shutdown_requested = True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Donk Collector Agent')
    parser.add_argument(
        '--hq-url',
        default='http://100.74.135.15:5000',
        help='HQ Pi WebSocket URL (default: http://100.74.135.15:5000)'
    )
    args = parser.parse_args()

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and run collector
    collector = DonkCollector(hq_url=args.hq_url)
    collector.run()


if __name__ == '__main__':
    main()
