"""
Context Aggregator for Donk Collector

Periodically collects context data from all loaded plugins
and sends updates to HQ Pi.
"""

import threading
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Callable

logger = logging.getLogger(__name__)


class ContextAggregator:
    """Manages periodic context collection from plugins"""

    def __init__(self, plugin_loader, send_callback: Callable):
        """
        Initialize context aggregator

        Args:
            plugin_loader: PluginLoader instance with loaded plugins
            send_callback: Function to call to send context updates
                          Should accept (plugin_id, context_data)
        """
        self.plugin_loader = plugin_loader
        self.send_callback = send_callback
        self.running = False
        self.thread = None
        self.last_update_times: Dict[str, float] = {}

        logger.info("Context aggregator initialized")

    def start(self):
        """Start the context aggregation thread"""
        if self.running:
            logger.warning("Context aggregator already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._aggregation_loop, daemon=True)
        self.thread.start()
        logger.info("Context aggregator started")

    def stop(self):
        """Stop the context aggregation thread"""
        if not self.running:
            return

        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Context aggregator stopped")

    def _aggregation_loop(self):
        """Main loop that periodically collects context from plugins"""
        logger.info("Context aggregation loop started")

        while self.running:
            try:
                current_time = time.time()
                plugins = self.plugin_loader.get_all_plugins()

                for plugin_id, plugin_info in plugins.items():
                    try:
                        # Check if it's time to update this plugin
                        update_interval = plugin_info.get("update_interval", 30)
                        last_update = self.last_update_times.get(plugin_id, 0)

                        if current_time - last_update >= update_interval:
                            self._collect_and_send(plugin_id, plugin_info)
                            self.last_update_times[plugin_id] = current_time

                    except Exception as e:
                        logger.error(f"Error collecting context from plugin {plugin_id}: {e}", exc_info=True)
                        # Continue with other plugins even if one fails

                # Sleep for 1 second before next check
                time.sleep(1)

            except Exception as e:
                logger.error(f"Error in aggregation loop: {e}", exc_info=True)
                time.sleep(1)

    def _collect_and_send(self, plugin_id: str, plugin_info: dict):
        """
        Collect context from a single plugin and send to HQ

        Args:
            plugin_id: Plugin identifier
            plugin_info: Plugin info dict containing instance
        """
        try:
            instance = plugin_info["instance"]

            # Call plugin's get_context method
            if not hasattr(instance, "get_context"):
                logger.warning(f"Plugin {plugin_id} does not have get_context method")
                return

            context_data = instance.get_context()

            # Only send if context data is not None
            if context_data is not None:
                logger.debug(f"Collected context from {plugin_id}: {context_data}")
                self.send_callback(plugin_id, context_data)
            else:
                logger.debug(f"Plugin {plugin_id} returned None context (likely inactive)")

        except Exception as e:
            logger.error(f"Error collecting context from {plugin_id}: {e}", exc_info=True)

    def request_immediate_update(self, plugin_id: str = None):
        """
        Request immediate context update for a specific plugin or all plugins

        Args:
            plugin_id: Specific plugin to update, or None for all plugins
        """
        try:
            if plugin_id:
                # Update single plugin
                plugin_info = self.plugin_loader.get_plugin(plugin_id)
                if plugin_info:
                    self._collect_and_send(plugin_id, plugin_info)
                    self.last_update_times[plugin_id] = time.time()
                    logger.info(f"Immediate update requested for plugin: {plugin_id}")
                else:
                    logger.warning(f"Plugin not found for immediate update: {plugin_id}")
            else:
                # Update all plugins
                plugins = self.plugin_loader.get_all_plugins()
                for pid, pinfo in plugins.items():
                    self._collect_and_send(pid, pinfo)
                    self.last_update_times[pid] = time.time()
                logger.info(f"Immediate update requested for all plugins ({len(plugins)} total)")

        except Exception as e:
            logger.error(f"Error during immediate update: {e}", exc_info=True)

    def execute_plugin_command(self, plugin_id: str, command_id: str, args: dict = None) -> dict:
        """
        Execute a command on a specific plugin

        Args:
            plugin_id: Plugin identifier
            command_id: Command to execute
            args: Optional command arguments

        Returns:
            Dict with success status and message
        """
        try:
            plugin_info = self.plugin_loader.get_plugin(plugin_id)
            if not plugin_info:
                return {
                    "success": False,
                    "message": f"Plugin not found: {plugin_id}"
                }

            instance = plugin_info["instance"]

            # Check if plugin supports commands
            if not hasattr(instance, "execute_command"):
                return {
                    "success": False,
                    "message": f"Plugin {plugin_id} does not support commands"
                }

            # Execute command
            result = instance.execute_command(command_id, args or {})

            logger.info(f"Executed command '{command_id}' on plugin {plugin_id}: {result}")

            # Trigger immediate context update after successful command
            if result.get("success"):
                logger.debug(f"Triggering immediate context update for {plugin_id} after command")
                self.request_immediate_update(plugin_id)

            return result

        except Exception as e:
            logger.error(f"Error executing command on plugin {plugin_id}: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error executing command: {str(e)}"
            }
