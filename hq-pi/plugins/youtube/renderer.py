"""
YouTube Tracker Plugin - Renderer

Renders YouTube viewing activity as widgets for the Donk UI
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class YouTubeRenderer:
    """Renders YouTube viewing context as UI widgets"""

    def __init__(self, config: dict):
        """
        Initialize YouTube renderer

        Args:
            config: Plugin manifest configuration
        """
        self.config = config
        logger.info("YouTube renderer initialized")

    def render(self, context_data: dict) -> List[Dict]:
        """
        Render YouTube context as widget list

        Args:
            context_data: Context from YouTubeCollector

        Returns:
            List of widget definitions
        """
        if not context_data or not context_data.get('active'):
            # YouTube not active, return empty list (section will disappear)
            return []

        widgets = []

        # Video Title Widget
        widgets.append({
            "type": "label",
            "text": context_data.get('video_title', 'Unknown Video'),
            "icon": "🎬",
            "color": "#FF0000",
            "size": "large"
        })

        # Channel Name Widget
        widgets.append({
            "type": "label",
            "text": f"Channel: {context_data.get('channel_name', 'Unknown')}",
            "icon": "📺",
            "color": "#888888"
        })

        # Video Position / Duration
        position = context_data.get('video_position', 'Unknown')
        duration = context_data.get('video_duration', 'Unknown')

        if position != 'Unknown' and duration != 'Unknown':
            progress_text = f"{position} / {duration}"
        else:
            progress_text = "Playing"

        widgets.append({
            "type": "label",
            "text": progress_text,
            "icon": "⏱️",
            "color": "#4CAF50"
        })

        # Session Duration
        session_seconds = context_data.get('session_duration_seconds', 0)
        session_time = self._format_duration(session_seconds)

        widgets.append({
            "type": "label",
            "text": f"Watching for: {session_time}",
            "icon": "⏰",
            "color": "#2196F3"
        })

        # Browser Info
        browser = context_data.get('browser', 'Unknown')
        widgets.append({
            "type": "label",
            "text": f"Browser: {browser}",
            "icon": "🌐",
            "color": "#666666"
        })

        return widgets

    def _format_duration(self, seconds: int) -> str:
        """
        Format duration in seconds to human readable format

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted string like "1h 23m 45s" or "5m 30s"
        """
        if seconds < 60:
            return f"{seconds}s"

        minutes = seconds // 60
        seconds = seconds % 60

        if minutes < 60:
            return f"{minutes}m {seconds}s"

        hours = minutes // 60
        minutes = minutes % 60

        return f"{hours}h {minutes}m {seconds}s"
