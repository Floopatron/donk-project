"""
Context Store for HQ Pi

In-memory storage for collector context data.
Stores latest context from each collector's plugins.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class ContextStore:
    """In-memory storage for collector context data"""

    def __init__(self):
        """Initialize empty context store"""
        # Structure: {device_id: {plugin_id: {data, timestamp}}}
        self.store: Dict[str, Dict[str, dict]] = {}
        logger.info("Context store initialized")

    def update_context(self, device_id: str, plugin_id: str, data: dict, timestamp: str = None):
        """
        Update context for a specific collector and plugin

        Args:
            device_id: Collector identifier
            plugin_id: Plugin identifier
            data: Context data
            timestamp: ISO format timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()

        # Ensure device_id exists in store
        if device_id not in self.store:
            self.store[device_id] = {}

        # Store context data
        self.store[device_id][plugin_id] = {
            "data": data,
            "timestamp": timestamp
        }

        logger.debug(f"Updated context: {device_id} / {plugin_id}")

    def get_context(self, device_id: str, plugin_id: str = None) -> Optional[dict]:
        """
        Get context for a specific collector and optionally a specific plugin

        Args:
            device_id: Collector identifier
            plugin_id: Plugin identifier (optional, returns all if None)

        Returns:
            Context dict or None if not found
        """
        if device_id not in self.store:
            return None

        if plugin_id:
            return self.store[device_id].get(plugin_id)
        else:
            return self.store[device_id]

    def get_all_context(self) -> Dict[str, Dict[str, dict]]:
        """
        Get all stored context

        Returns:
            Complete context store
        """
        return self.store

    def get_device_context(self, device_id: str) -> Dict[str, dict]:
        """
        Get all plugin context for a specific device

        Args:
            device_id: Collector identifier

        Returns:
            Dict of plugin contexts or empty dict
        """
        return self.store.get(device_id, {})

    def get_plugin_context_all_devices(self, plugin_id: str) -> Dict[str, dict]:
        """
        Get context for a specific plugin across all devices

        Args:
            plugin_id: Plugin identifier

        Returns:
            Dict mapping device_id to plugin context
        """
        result = {}
        for device_id, plugins in self.store.items():
            if plugin_id in plugins:
                result[device_id] = plugins[plugin_id]
        return result

    def remove_device(self, device_id: str):
        """
        Remove all context for a device (e.g., when disconnected)

        Args:
            device_id: Collector identifier
        """
        if device_id in self.store:
            del self.store[device_id]
            logger.info(f"Removed context for device: {device_id}")

    def remove_plugin_context(self, device_id: str, plugin_id: str):
        """
        Remove context for a specific plugin on a device

        Args:
            device_id: Collector identifier
            plugin_id: Plugin identifier
        """
        if device_id in self.store and plugin_id in self.store[device_id]:
            del self.store[device_id][plugin_id]
            logger.debug(f"Removed plugin context: {device_id} / {plugin_id}")

    def get_devices_with_plugin(self, plugin_id: str) -> List[str]:
        """
        Get list of device IDs that have context for a specific plugin

        Args:
            plugin_id: Plugin identifier

        Returns:
            List of device IDs
        """
        devices = []
        for device_id, plugins in self.store.items():
            if plugin_id in plugins:
                devices.append(device_id)
        return devices

    def clear(self):
        """Clear all stored context"""
        self.store = {}
        logger.info("Context store cleared")

    def get_stats(self) -> dict:
        """
        Get statistics about stored context

        Returns:
            Dict with stats
        """
        total_devices = len(self.store)
        total_plugins = sum(len(plugins) for plugins in self.store.values())

        plugin_counts = {}
        for plugins in self.store.values():
            for plugin_id in plugins.keys():
                plugin_counts[plugin_id] = plugin_counts.get(plugin_id, 0) + 1

        return {
            "total_devices": total_devices,
            "total_plugin_contexts": total_plugins,
            "plugin_counts": plugin_counts
        }
