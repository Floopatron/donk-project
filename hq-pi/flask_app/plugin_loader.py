"""
Plugin Loader for HQ Pi

Discovers and loads renderer plugins from the plugins directory.
Each plugin must have a manifest.json and renderer.py file.
"""

import os
import json
import importlib.util
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PluginLoader:
    """Manages loading and instantiation of renderer plugins"""

    def __init__(self, plugins_dir: str = None):
        """
        Initialize the plugin loader

        Args:
            plugins_dir: Path to plugins directory (defaults to ../plugins)
        """
        if plugins_dir is None:
            # Default to hq-pi/plugins directory
            base_dir = Path(__file__).parent.parent
            plugins_dir = base_dir / "plugins"

        self.plugins_dir = Path(plugins_dir)
        self.loaded_plugins: Dict[str, dict] = {}

        logger.info(f"Plugin loader initialized with directory: {self.plugins_dir}")

    def discover_plugins(self) -> List[str]:
        """
        Discover all available plugins in the plugins directory

        Returns:
            List of plugin directory names
        """
        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory does not exist: {self.plugins_dir}")
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
            return []

        plugins = []
        for item in self.plugins_dir.iterdir():
            if item.is_dir() and (item / "manifest.json").exists():
                plugins.append(item.name)

        logger.info(f"Discovered {len(plugins)} plugins: {plugins}")
        return plugins

    def load_manifest(self, plugin_name: str) -> Optional[dict]:
        """
        Load and validate plugin manifest

        Args:
            plugin_name: Name of the plugin directory

        Returns:
            Manifest dict or None if invalid
        """
        manifest_path = self.plugins_dir / plugin_name / "manifest.json"

        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)

            # Validate required fields
            required_fields = ["plugin_id", "version", "name", "renderer"]
            for field in required_fields:
                if field not in manifest:
                    logger.error(f"Plugin {plugin_name}: Missing required field '{field}' in manifest")
                    return None

            # Validate renderer section
            renderer_config = manifest.get("renderer", {})
            if "file" not in renderer_config or "class" not in renderer_config:
                logger.error(f"Plugin {plugin_name}: Invalid renderer configuration")
                return None

            logger.info(f"Loaded manifest for plugin: {manifest['plugin_id']} v{manifest['version']}")
            return manifest

        except json.JSONDecodeError as e:
            logger.error(f"Plugin {plugin_name}: Invalid JSON in manifest: {e}")
            return None
        except Exception as e:
            logger.error(f"Plugin {plugin_name}: Error loading manifest: {e}")
            return None

    def load_plugin_class(self, plugin_name: str, manifest: dict):
        """
        Dynamically import and instantiate plugin class

        Args:
            plugin_name: Name of the plugin directory
            manifest: Plugin manifest dict

        Returns:
            Plugin instance or None if failed
        """
        renderer_config = manifest["renderer"]
        plugin_file = renderer_config["file"]
        class_name = renderer_config["class"]

        plugin_path = self.plugins_dir / plugin_name / plugin_file

        if not plugin_path.exists():
            logger.error(f"Plugin {plugin_name}: Renderer file not found: {plugin_file}")
            return None

        try:
            # Load module dynamically
            spec = importlib.util.spec_from_file_location(
                f"donk_renderer_{plugin_name}",
                plugin_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Get the plugin class
            if not hasattr(module, class_name):
                logger.error(f"Plugin {plugin_name}: Class '{class_name}' not found in {plugin_file}")
                return None

            plugin_class = getattr(module, class_name)

            # Instantiate with manifest config
            plugin_instance = plugin_class(manifest)

            logger.info(f"Successfully loaded plugin class: {plugin_name}.{class_name}")
            return plugin_instance

        except Exception as e:
            logger.error(f"Plugin {plugin_name}: Error loading class: {e}", exc_info=True)
            return None

    def load_all_plugins(self) -> Dict[str, dict]:
        """
        Discover and load all available plugins

        Returns:
            Dict of loaded plugins: {plugin_id: {manifest, instance, name}}
        """
        plugin_names = self.discover_plugins()

        for plugin_name in plugin_names:
            try:
                # Load manifest
                manifest = self.load_manifest(plugin_name)
                if manifest is None:
                    continue

                plugin_id = manifest["plugin_id"]

                # Check if already loaded
                if plugin_id in self.loaded_plugins:
                    logger.warning(f"Plugin {plugin_id} already loaded, skipping duplicate")
                    continue

                # Load plugin class
                instance = self.load_plugin_class(plugin_name, manifest)
                if instance is None:
                    continue

                # Store loaded plugin
                self.loaded_plugins[plugin_id] = {
                    "manifest": manifest,
                    "instance": instance,
                    "name": plugin_name
                }

                logger.info(f"✓ Plugin loaded: {plugin_id} ({manifest['name']})")

            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_name}: {e}", exc_info=True)
                continue

        logger.info(f"Loaded {len(self.loaded_plugins)} renderer plugins total")
        return self.loaded_plugins

    def get_plugin(self, plugin_id: str) -> Optional[dict]:
        """
        Get a loaded plugin by ID

        Args:
            plugin_id: The plugin's unique identifier

        Returns:
            Plugin dict or None if not found
        """
        return self.loaded_plugins.get(plugin_id)

    def get_all_plugins(self) -> Dict[str, dict]:
        """
        Get all loaded plugins

        Returns:
            Dict of all loaded plugins
        """
        return self.loaded_plugins

    def render_plugin_widgets(self, plugin_id: str, context_data: dict) -> Optional[list]:
        """
        Render widgets for a specific plugin

        Args:
            plugin_id: Plugin identifier
            context_data: Context data from collector

        Returns:
            List of widget dicts or None if plugin not found
        """
        plugin_info = self.get_plugin(plugin_id)
        if not plugin_info:
            logger.warning(f"Cannot render widgets for unknown plugin: {plugin_id}")
            return None

        try:
            instance = plugin_info["instance"]

            if not hasattr(instance, "render"):
                logger.warning(f"Plugin {plugin_id} does not have render method")
                return None

            widgets = instance.render(context_data)
            return widgets

        except Exception as e:
            logger.error(f"Error rendering widgets for plugin {plugin_id}: {e}", exc_info=True)
            return None
