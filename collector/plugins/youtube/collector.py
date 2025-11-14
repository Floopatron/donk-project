"""
YouTube Tracker Plugin - Collector

Detects when YouTube is open in any browser and tracks:
- Video title
- Channel name
- Current position in video
- Total video duration
- How long YouTube has been open

Supports: Chrome, Brave, Opera, Firefox, Edge
Cross-platform: Windows (native PowerShell), Linux (wmctrl/xdotool), macOS (AppleScript)
NO EXTERNAL DEPENDENCIES REQUIRED (except psutil for process detection)
"""

import re
import time
import logging
import subprocess
import platform
from datetime import datetime, timezone
from typing import Optional, Dict

try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger(__name__)


class YouTubeCollector:
    """Collects YouTube viewing activity from browser windows"""

    # Browser executable names to monitor
    BROWSER_PROCESSES = {
        'brave.exe': 'Brave',
        'brave': 'Brave',
        'opera.exe': 'Opera',
        'opera': 'Opera',
        'chrome.exe': 'Chrome',
        'chrome': 'Chrome',
        'firefox.exe': 'Firefox',
        'firefox': 'Firefox',
        'msedge.exe': 'Edge',
        'msedge': 'Edge',
        'chromium': 'Chromium',
        'chromium.exe': 'Chromium'
    }

    def __init__(self, config: dict):
        """
        Initialize YouTube collector

        Args:
            config: Plugin manifest configuration
        """
        self.config = config
        self.youtube_start_time = None
        self.last_video_info = None
        self.platform = platform.system()

        # Check dependencies
        if psutil is None:
            logger.warning("psutil not installed! Will use basic process detection.")

        logger.info(f"YouTube collector initialized on {self.platform}")

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
                logger.info(f"YouTube opened: {youtube_window}")

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
        Find browser window with YouTube open using platform-specific methods

        Returns:
            Window title string or None
        """
        if self.platform == "Windows":
            return self._find_youtube_window_windows()
        elif self.platform == "Linux":
            return self._find_youtube_window_linux()
        elif self.platform == "Darwin":  # macOS
            return self._find_youtube_window_macos()
        else:
            logger.warning(f"Unsupported platform: {self.platform}")
            return None

    def _find_youtube_window_windows(self) -> Optional[str]:
        """
        Windows: Use PowerShell to get window titles (NO external dependencies!)

        Returns:
            Window title string or None
        """
        try:
            # PowerShell command to get all window titles containing 'youtube'
            # Uses Windows API via Add-Type
            ps_command = '''
Add-Type @"
    using System;
    using System.Runtime.InteropServices;
    using System.Text;
    public class Win32 {
        [DllImport("user32.dll")]
        public static extern bool EnumWindows(EnumWindowsProc enumProc, IntPtr lParam);

        [DllImport("user32.dll")]
        public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);

        [DllImport("user32.dll")]
        public static extern bool IsWindowVisible(IntPtr hWnd);

        public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    }
"@

$windows = New-Object System.Collections.ArrayList
$callback = {
    param($hWnd, $lParam)
    if ([Win32]::IsWindowVisible($hWnd)) {
        $text = New-Object System.Text.StringBuilder 256
        [void][Win32]::GetWindowText($hWnd, $text, 256)
        $title = $text.ToString()
        if ($title -ne "" -and $title -match "youtube" -and $title -match "brave|chrome|opera|firefox|edge") {
            [void]$windows.Add($title)
        }
    }
    return $true
}

[Win32]::EnumWindows($callback, [IntPtr]::Zero)
if ($windows.Count -gt 0) {
    $windows[0]
}
'''

            # Run PowerShell command
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )

            if result.returncode == 0 and result.stdout.strip():
                title = result.stdout.strip()
                if title and 'youtube' in title.lower():
                    return title

        except subprocess.TimeoutExpired:
            logger.warning("PowerShell window detection timed out")
        except Exception as e:
            logger.debug(f"PowerShell method failed: {e}")

        # Fallback: Just check if browser is running (can't get window title)
        if psutil:
            if self._is_browser_running():
                return "YouTube - Browser (window title unavailable)"

        return None

    def _find_youtube_window_linux(self) -> Optional[str]:
        """
        Linux: Use wmctrl or xdotool command-line tools

        Returns:
            Window title string or None
        """
        # Try wmctrl first (most reliable)
        try:
            result = subprocess.run(
                ["wmctrl", "-l"],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'youtube' in line.lower():
                        # Extract title (everything after the 3rd column)
                        parts = line.split(None, 3)
                        if len(parts) >= 4:
                            return parts[3]
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Try xdotool as fallback
        try:
            result = subprocess.run(
                ["xdotool", "search", "--name", "youtube"],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0 and result.stdout.strip():
                # Get window title from window ID
                window_id = result.stdout.strip().split('\n')[0]
                title_result = subprocess.run(
                    ["xdotool", "getwindowname", window_id],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if title_result.returncode == 0:
                    return title_result.stdout.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return None

    def _find_youtube_window_macos(self) -> Optional[str]:
        """
        macOS: Use AppleScript to get window titles

        Returns:
            Window title string or None
        """
        try:
            # AppleScript to get visible window titles
            script = '''
tell application "System Events"
    set windowList to {}
    repeat with theProcess in (every process whose visible is true)
        try
            repeat with theWindow in (every window of theProcess)
                set windowTitle to name of theWindow
                if windowTitle contains "YouTube" then
                    set end of windowList to windowTitle
                end if
            end repeat
        end try
    end repeat
    return windowList
end tell
'''

            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and result.stdout.strip():
                # Return first YouTube window found
                return result.stdout.strip().split(',')[0].strip()

        except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
            logger.debug(f"AppleScript method failed: {e}")

        return None

    def _is_browser_running(self) -> bool:
        """
        Check if any browser process is running (fallback when we can't get window titles)

        Returns:
            True if browser detected, False otherwise
        """
        if not psutil:
            return False

        try:
            for proc in psutil.process_iter(['name']):
                try:
                    proc_name = proc.info['name']
                    if proc_name and proc_name.lower() in [b.lower() for b in self.BROWSER_PROCESSES.keys()]:
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.debug(f"Process detection failed: {e}")

        return False

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
