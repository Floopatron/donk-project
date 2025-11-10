"""
YouTube Tracker Plugin - Collector

Detects when YouTube is open in any browser and tracks:
- Video title
- Channel name
- Current position in video
- Total video duration
- How long YouTube has been open

Supports: Chrome, Brave, Opera, Firefox, Edge
"""

import re
import time
import logging
from datetime import datetime, timezone
from typing import Optional, Dict

try:
    import psutil
except ImportError:
    psutil = None

try:
    import pygetwindow as gw
except ImportError:
    gw = None

logger = logging.getLogger(__name__)


class YouTubeCollector:
    """Collects YouTube viewing activity from browser windows"""

    # Browser executable names to monitor
    BROWSER_PROCESSES = [
        'brave.exe', 'brave',
        'opera.exe', 'opera',
        'chrome.exe', 'chrome',
        'firefox.exe', 'firefox',
        'msedge.exe', 'msedge',
        'chromium', 'chromium.exe'
    ]

    def __init__(self, config: dict):
        """
        Initialize YouTube collector

        Args:
            config: Plugin manifest configuration
        """
        self.config = config
        self.youtube_start_time = None
        self.last_video_info = None

        # Check dependencies
        if psutil is None:
            logger.error("psutil not installed! YouTube plugin will not function.")
        if gw is None:
            logger.warning("pygetwindow not installed! Will use basic window detection.")

        logger.info("YouTube collector initialized")

    def get_context(self) -> Optional[Dict]:
        """
        Get current YouTube viewing context

        Returns:
            Context dict with YouTube info, or None if YouTube not active
        """
        try:
            youtube_window = self._find_youtube_window()

            if youtube_window is None:
                # YouTube not active
                if self.youtube_start_time is not None:
                    logger.info("YouTube closed")
                    self.youtube_start_time = None
                    self.last_video_info = None
                return None

            # YouTube is active
            if self.youtube_start_time is None:
                self.youtube_start_time = time.time()
                logger.info("YouTube opened")

            # Extract video info from window title
            video_info = self._parse_window_title(youtube_window)

            # Calculate session duration
            session_duration = int(time.time() - self.youtube_start_time)

            context = {
                "active": True,
                "video_title": video_info.get('title', 'Unknown'),
                "channel_name": video_info.get('channel', 'Unknown'),
                "video_position": video_info.get('position', 'Unknown'),
                "video_duration": video_info.get('duration', 'Unknown'),
                "session_duration_seconds": session_duration,
                "browser": video_info.get('browser', 'Unknown'),
                "window_title": youtube_window,
                "detected_at": datetime.now(timezone.utc).isoformat()
            }

            self.last_video_info = context
            return context

        except Exception as e:
            logger.error(f"Error getting YouTube context: {e}", exc_info=True)
            return self.last_video_info  # Return last known state on error

    def _find_youtube_window(self) -> Optional[str]:
        """
        Find browser window with YouTube open

        Returns:
            Window title string or None
        """
        if gw is None and psutil is None:
            return None

        try:
            # Method 1: Use pygetwindow (works on Windows)
            if gw is not None:
                try:
                    windows = gw.getAllTitles()
                    for title in windows:
                        if 'youtube' in title.lower() and any(browser in title.lower() for browser in ['chrome', 'brave', 'opera', 'firefox', 'edge']):
                            return title
                except Exception as e:
                    logger.debug(f"pygetwindow failed: {e}")

            # Method 2: Check running browser processes (fallback)
            if psutil is not None:
                for proc in psutil.process_iter(['name', 'cmdline']):
                    try:
                        if proc.info['name'] and proc.info['name'].lower() in [b.lower() for b in self.BROWSER_PROCESSES]:
                            # Browser is running, try to get window title via psutil
                            # This is limited but better than nothing
                            try:
                                # On some systems, we can check if browser has focus
                                if gw:
                                    active_window = gw.getActiveWindow()
                                    if active_window and 'youtube' in active_window.title.lower():
                                        return active_window.title
                            except:
                                pass
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

        except Exception as e:
            logger.error(f"Error finding YouTube window: {e}", exc_info=True)

        return None

    def _parse_window_title(self, window_title: str) -> Dict:
        """
        Parse YouTube video information from browser window title

        Typical formats:
        - "Video Title - YouTube - Brave"
        - "(123) Video Title - YouTube - Chrome"
        - "Video Title - Channel Name - YouTube - Firefox"

        Args:
            window_title: Browser window title

        Returns:
            Dict with parsed info
        """
        info = {
            'title': 'Unknown',
            'channel': 'Unknown',
            'position': 'Unknown',
            'duration': 'Unknown',
            'browser': 'Unknown'
        }

        try:
            # Detect browser
            for browser in ['Brave', 'Opera', 'Chrome', 'Firefox', 'Edge', 'Chromium']:
                if browser.lower() in window_title.lower():
                    info['browser'] = browser
                    break

            # Remove notification count like "(123) "
            title = re.sub(r'^\(\d+\)\s*', '', window_title)

            # Split by " - "
            parts = title.split(' - ')

            if len(parts) >= 2:
                # First part is usually video title
                info['title'] = parts[0].strip()

                # Look for "YouTube" in parts
                youtube_index = -1
                for i, part in enumerate(parts):
                    if 'youtube' in part.lower():
                        youtube_index = i
                        break

                # If we found YouTube and there's a part before it (not the title)
                if youtube_index > 1:
                    # The part before YouTube might be channel name
                    info['channel'] = parts[youtube_index - 1].strip()

            # Try to detect if video is paused (some browsers show this)
            if 'paused' in title.lower():
                info['position'] = 'Paused'

        except Exception as e:
            logger.warning(f"Error parsing window title: {e}")

        return info

    def execute_command(self, command_id: str, args: dict) -> dict:
        """
        Execute command (YouTube plugin has no commands currently)

        Args:
            command_id: Command identifier
            args: Command arguments

        Returns:
            Result dict
        """
        return {
            "success": False,
            "message": "YouTube plugin does not support commands"
        }
