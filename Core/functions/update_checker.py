# Core/functions/update_checker.py
# Checks GitHub for a new app release once at startup.
# Runs in a background thread to avoid blocking the UI.
import json
import os
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from typing import Callable

from Core.paths import get_app_path, get_data_path
from Core.version import APP_VERSION, GITHUB_REPO, GITHUB_RELEASES_URL

_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
_TIMEOUT = 5  # seconds
_NOTIFIED_FILE = "update_notified.json"


# ---------------------------------------------------------------------------
# Version helpers
# ---------------------------------------------------------------------------

def _parse_version(tag: str) -> tuple[int, ...]:
    """Convert 'v1.2.3' or '1.2.3' to (1, 2, 3) for comparison."""
    tag = tag.lstrip("v")
    try:
        return tuple(int(x) for x in tag.split("."))
    except ValueError:
        return (0,)


# ---------------------------------------------------------------------------
# Notified-version persistence (toast shown once per discovered version)
# ---------------------------------------------------------------------------

def _get_last_notified_version() -> str | None:
    path = get_data_path(_NOTIFIED_FILE)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f).get("version")
    except Exception:
        return None


def _save_notified_version(version: str) -> None:
    os.makedirs(get_data_path(), exist_ok=True)
    path = get_data_path(_NOTIFIED_FILE)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"version": version}, f, indent=4)


# ---------------------------------------------------------------------------
# Toast notification
# ---------------------------------------------------------------------------

def _get_icon_path() -> str | None:
    if hasattr(sys, "_MEIPASS"):
        p = os.path.join(sys._MEIPASS, "Assets", "icons", "icon.ico")
    else:
        # get_app_path() == src/ in dev mode
        p = os.path.join(get_app_path(), "Assets", "icons", "icon.ico")
    return p if os.path.exists(p) else None


def _show_update_toast(version: str, url: str) -> None:
    """
    Show a Windows 10/11 toast notification.
    Falls back to PowerShell if win11toast is not installed.
    """
    try:
        from win11toast import toast  # type: ignore
        kwargs: dict = {"on_click": url}
        icon_path = _get_icon_path()
        if icon_path:
            kwargs["icon"] = {"src": icon_path, "placement": "appLogoOverride"}
        toast(
            "Premiere Companion — Update Available",
            f"Version {version} is available. Click to download.",
            **kwargs,
        )
    except ImportError:
        _show_powershell_toast(version, url)
    except Exception:
        pass


def _show_powershell_toast(version: str, url: str) -> None:
    """PowerShell-based toast fallback (no extra dependency)."""
    script = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

$xml = @"
<toast activationType="protocol" launch="{url}">
  <visual>
    <binding template="ToastGeneric">
      <text>Premiere Companion - Update Available</text>
      <text>Version {version} is available. Click to download.</text>
    </binding>
  </visual>
  <actions>
    <action content="Download" activationType="protocol" arguments="{url}" />
  </actions>
</toast>
"@

$doc = New-Object Windows.Data.Xml.Dom.XmlDocument
$doc.LoadXml($xml)
$toast = New-Object Windows.UI.Notifications.ToastNotification $doc
$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Premiere Companion")
$notifier.Show($toast)
"""
    try:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden",
             "-ExecutionPolicy", "Bypass", "-Command", script],
            creationflags=0x08000000,  # CREATE_NO_WINDOW
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------

def _check_worker(log_cb: Callable[[str, str], None] | None) -> None:
    """
    Fetch the latest GitHub release and:
    - Always log to console if an update is available.
    - Show a toast only the first time a given version is discovered.
    """
    try:
        req = urllib.request.Request(
            _API_URL,
            headers={"User-Agent": f"Premiere-Companion/{APP_VERSION}"},
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))

        latest_tag = data.get("tag_name", "")
        html_url = data.get("html_url", GITHUB_RELEASES_URL)

        if not latest_tag:
            return

        if _parse_version(latest_tag) <= _parse_version(APP_VERSION):
            return  # already up to date

        version_str = latest_tag.lstrip("v")

        # Always log to console
        if log_cb:
            log_cb(
                f" Update available: v{version_str}  —  {html_url}",
                "#55ccff",  # info color
            )

        # Toast only once per discovered version
        if _get_last_notified_version() != version_str:
            _show_update_toast(version_str, html_url)
            _save_notified_version(version_str)

    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        pass
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def start_update_check(log_cb: Callable[[str, str], None] | None = None) -> None:
    """
    Launch the update check in a daemon thread.
    log_cb(message, color) is called on the main-thread-safe log if provided.
    Returns immediately.
    """
    t = threading.Thread(
        target=_check_worker,
        args=(log_cb,),
        daemon=True,
        name="UpdateCheck",
    )
    t.start()
