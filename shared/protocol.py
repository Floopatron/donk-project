"""
Donk WebSocket Protocol Definitions

Defines message types and structures used for communication between:
- HQ Pi (server)
- Collectors (desktop agents)
- Donk (handheld client)

All messages are JSON objects with a "type" field.
"""

from typing import Dict, Any, Optional
from datetime import datetime


class MessageType:
    """WebSocket message types"""

    # Collector → HQ Pi
    COLLECTOR_REGISTER = "collector_register"
    COLLECTOR_HEARTBEAT = "collector_heartbeat"
    CONTEXT_UPDATE = "context_update"
    COMMAND_RESULT = "command_result"

    # HQ Pi → Collector
    COMMAND = "command"
    CONFIG_UPDATE = "config_update"

    # HQ Pi → Donk
    PAGE_UPDATE = "page_update"
    COLLECTOR_LIST = "collector_list"

    # Donk → HQ Pi
    DONK_REGISTER = "donk_register"
    BUTTON_PRESS = "button_press"

    # Bidirectional
    PING = "ping"
    PONG = "pong"
    ERROR = "error"


def create_collector_register(device_id: str, hostname: str, platform: str) -> Dict[str, Any]:
    """
    Create a collector registration message

    Args:
        device_id: Unique collector identifier
        hostname: Device hostname
        platform: OS platform (Linux, Windows, Darwin)

    Returns:
        Registration message dict
    """
    return {
        "type": MessageType.COLLECTOR_REGISTER,
        "device_id": device_id,
        "hostname": hostname,
        "platform": platform,
        "timestamp": datetime.utcnow().isoformat()
    }


def create_collector_heartbeat(device_id: str) -> Dict[str, Any]:
    """
    Create a heartbeat message

    Args:
        device_id: Collector identifier

    Returns:
        Heartbeat message dict
    """
    return {
        "type": MessageType.COLLECTOR_HEARTBEAT,
        "device_id": device_id,
        "timestamp": datetime.utcnow().isoformat()
    }


def create_context_update(device_id: str, plugin_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a context update message from collector plugin

    Args:
        device_id: Collector identifier
        plugin_id: Plugin identifier
        data: Plugin-specific context data

    Returns:
        Context update message dict
    """
    return {
        "type": MessageType.CONTEXT_UPDATE,
        "device_id": device_id,
        "plugin_id": plugin_id,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }


def create_command(device_id: str, plugin_id: str, command_id: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a command message to collector

    Args:
        device_id: Target collector
        plugin_id: Target plugin
        command_id: Command to execute
        args: Command arguments (optional)

    Returns:
        Command message dict
    """
    return {
        "type": MessageType.COMMAND,
        "device_id": device_id,
        "plugin_id": plugin_id,
        "command_id": command_id,
        "args": args or {},
        "timestamp": datetime.utcnow().isoformat()
    }


def create_command_result(device_id: str, plugin_id: str, command_id: str, success: bool, message: str, request_id: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a command result message

    Args:
        device_id: Collector identifier
        plugin_id: Plugin identifier
        command_id: ID of executed command
        success: Whether command succeeded
        message: Result message
        request_id: Optional request ID for tracking
        data: Additional result data (optional)

    Returns:
        Command result message dict
    """
    return {
        "type": MessageType.COMMAND_RESULT,
        "device_id": device_id,
        "plugin_id": plugin_id,
        "command_id": command_id,
        "success": success,
        "message": message,
        "request_id": request_id,
        "data": data or {},
        "timestamp": datetime.utcnow().isoformat()
    }


def create_collector_list(collectors: list) -> Dict[str, Any]:
    """
    Create a message with list of connected collectors

    Args:
        collectors: List of collector info dicts

    Returns:
        Collector list message dict
    """
    return {
        "type": MessageType.COLLECTOR_LIST,
        "collectors": collectors,
        "count": len(collectors),
        "timestamp": datetime.utcnow().isoformat()
    }


def create_error(message: str, details: Optional[str] = None) -> Dict[str, Any]:
    """
    Create an error message

    Args:
        message: Error message
        details: Additional error details (optional)

    Returns:
        Error message dict
    """
    return {
        "type": MessageType.ERROR,
        "message": message,
        "details": details,
        "timestamp": datetime.utcnow().isoformat()
    }


def validate_message(msg: Dict[str, Any]) -> bool:
    """
    Validate that a message has required fields

    Args:
        msg: Message dictionary

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(msg, dict):
        return False

    if "type" not in msg:
        return False

    if "timestamp" not in msg:
        return False

    return True
