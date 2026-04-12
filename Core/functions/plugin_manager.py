# Core/functions/plugin_manager.py
# Handles install/uninstall of the bundled UXP plugin via Adobe's UPI.
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

from Core.paths import get_app_path

_EXCLUDE_PATTERNS = {".git", ".gitignore", "node_modules", ".DS_Store", "__pycache__"}

PLUGIN_NAME = "Premiere Companion (Listener)"
ADOBE_SERVICE_NAME = "AdobeUpdateService"
UPI_PATH = (
    r"C:\Program Files\Common Files\Adobe\Adobe Desktop Common"
    r"\RemoteComponents\UPI\UnifiedPluginInstallerAgent"
    r"\UnifiedPluginInstallerAgent.exe"
)
# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_plugin_folder() -> str:
    """
    Return the folder that contains the .ccx file.

    Frozen (compiled):  <_MEIPASS>/Plugin/
    Dev (script):       src/              (get_app_path() == src/)
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "Plugin")
    # get_app_path() returns src/ in dev mode — .ccx lives at the src/ root
    return get_app_path()


def _get_plugin_src_dir() -> str:
    """Return the plugin source directory (always src/Plugin/ in dev mode)."""
    return os.path.join(get_app_path(), "Plugin")


def _find_bundled_ccx() -> str | None:
    """Return the path to the bundled .ccx, or None if not found."""
    folder = _get_plugin_folder()
    if not os.path.isdir(folder):
        return None
    for f in os.listdir(folder):
        if f.endswith(".ccx"):
            return os.path.join(folder, f)
    return None


def _build_ccx_dev() -> str | None:
    """
    Dev mode only: build a .ccx from src/Plugin/ (source) into src/ (output).
    Deletes any existing .ccx in src/ first.
    Returns the new .ccx path, or None on error.
    """
    src_dir = _get_plugin_src_dir()   # src/Plugin/
    out_dir = _get_plugin_folder()    # src/

    if not os.path.isdir(src_dir):
        return None

    manifest_path = os.path.join(src_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        return None

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        plugin_id = manifest["id"]
        plugin_version = manifest["version"]
    except Exception:
        return None

    ccx_name = f"{plugin_id}_{plugin_version}.ccx"
    ccx_path = os.path.join(out_dir, ccx_name)

    # Remove old .ccx files from src/
    for entry in os.listdir(out_dir):
        if entry.endswith(".ccx"):
            os.remove(os.path.join(out_dir, entry))

    # Stage plugin source (copy src/Plugin/ → temp staging)
    staging = os.path.join(out_dir, "_ccx_staging")
    if os.path.exists(staging):
        shutil.rmtree(staging)
    os.makedirs(staging)

    for item in os.listdir(src_dir):
        if item in _EXCLUDE_PATTERNS or item.endswith(".ccx"):
            continue
        s = os.path.join(src_dir, item)
        d = os.path.join(staging, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, ignore=shutil.ignore_patterns(*_EXCLUDE_PATTERNS))
        else:
            shutil.copy2(s, d)

    # Zip staging → .ccx
    with zipfile.ZipFile(ccx_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(staging):
            dirs[:] = [d for d in dirs if d not in _EXCLUDE_PATTERNS]
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, staging)
                zf.write(abs_path, rel_path)

    shutil.rmtree(staging)
    return ccx_path


def ensure_ccx_built() -> None:
    """
    Dev mode only: build the .ccx from src/Plugin/ into src/ if missing or outdated.
    No-op when running as a compiled .exe (the .ccx is already bundled).
    """
    if hasattr(sys, "_MEIPASS"):
        return  # compiled: .ccx is pre-bundled, nothing to do

    manifest_path = os.path.join(_get_plugin_src_dir(), "manifest.json")
    if not os.path.exists(manifest_path):
        return

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        expected_ccx = os.path.join(
            _get_plugin_folder(),
            f"{manifest['id']}_{manifest['version']}.ccx",
        )
        if os.path.exists(expected_ccx):
            return  # already up to date
    except Exception:
        return

    _build_ccx_dev()


def _run_upi(args: list[str]) -> tuple[int, str]:
    """Run UnifiedPluginInstallerAgent with given args. Returns (returncode, output)."""
    cmd = [UPI_PATH] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return result.returncode, (result.stdout + result.stderr).strip()
    except FileNotFoundError:
        return -1, f"UPI not found: {UPI_PATH}"
    except subprocess.TimeoutExpired:
        return -1, "UPI timed out after 60s"
    except Exception as e:
        return -1, str(e)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_bundled_plugin_version() -> str | None:
    """
    Read the plugin version from manifest.json inside the bundled .ccx.
    The .ccx is a zip archive — no need to bundle manifest.json separately.
    """
    ccx_path = _find_bundled_ccx()
    if not ccx_path:
        return None
    try:
        with zipfile.ZipFile(ccx_path, "r") as zf:
            with zf.open("manifest.json") as f:
                return json.loads(f.read().decode("utf-8")).get("version")
    except Exception:
        return None


def get_installed_plugin_version() -> str | None:
    """
    Query Adobe UPI for the actually installed version of the plugin.
    Runs `UPI /list all` and parses the output to find PLUGIN_NAME.
    Returns the version string, or None if not installed / UPI unavailable.
    """
    if not is_upi_available():
        return None
    try:
        result = subprocess.run(
            [UPI_PATH, "/list", "all"],
            capture_output=True, text=True, timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        for line in (result.stdout + result.stderr).splitlines():
            if PLUGIN_NAME in line:
                # Version is the last whitespace-separated token on the line
                # e.g. "Enabled    Premiere Companion (Listener)    1.0.1"
                parts = line.split()
                if parts:
                    candidate = parts[-1]
                    if re.match(r"^\d+\.\d+", candidate):
                        return candidate
    except Exception:
        pass
    return None


def is_plugin_update_needed() -> bool:
    """
    True if the plugin is installed AND its version differs from the bundled one.
    Returns False when the plugin is not installed (None) — no false alarm.
    """
    bundled = get_bundled_plugin_version()
    installed = get_installed_plugin_version()
    if not bundled or installed is None:
        return False
    return bundled != installed


def is_upi_available() -> bool:
    return os.path.exists(UPI_PATH)


def ensure_adobe_service(log_cb=None) -> bool:
    """
    Check if AdobeUpdateService is running; start it if not.
    Returns True on success, False on failure.
    """
    def _log(msg: str) -> None:
        if log_cb:
            log_cb(msg)

    try:
        result = subprocess.run(
            ["sc", "query", ADOBE_SERVICE_NAME],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if "RUNNING" in result.stdout:
            _log(f" {ADOBE_SERVICE_NAME} is already running.")
            return True

        _log(f" {ADOBE_SERVICE_NAME} is not running — starting it...")
        start = subprocess.run(
            ["sc", "start", ADOBE_SERVICE_NAME],
            capture_output=True, text=True, timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if start.returncode == 0 or "START_PENDING" in start.stdout:
            _log(f" {ADOBE_SERVICE_NAME} started.")
            return True

        _log(f" Failed to start {ADOBE_SERVICE_NAME}: {start.stderr.strip()}")
        return False

    except Exception as e:
        _log(f" Error checking Adobe service: {e}")
        return False


def install_plugin(log_cb=None) -> bool:
    """
    Install the bundled plugin via UPI.
    1. Ensure AdobeUpdateService is running.
    2. Remove any previous version silently.
    3. Install the bundled .ccx.
    4. Save the installed version on success.
    Returns True on success.
    """
    def _log(msg: str) -> None:
        if log_cb:
            log_cb(msg)

    if not is_upi_available():
        _log(f" Adobe UPI not found at expected path.")
        _log(f"   {UPI_PATH}")
        return False

    ccx_path = _find_bundled_ccx()
    if not ccx_path:
        _log(" No .ccx file found in the Plugin folder.")
        return False

    _log(f" Found plugin: {os.path.basename(ccx_path)}")

    # Step 1 — ensure service
    if not ensure_adobe_service(log_cb):
        _log(" Cannot proceed without AdobeUpdateService.")
        return False

    # Step 2 — silent remove (ignore errors: plugin may not be installed yet)
    _log(f" Removing previous version of '{PLUGIN_NAME}'...")
    _run_upi(["/remove", PLUGIN_NAME])

    # Step 3 — install
    _log(f" Installing '{os.path.basename(ccx_path)}'...")
    code, output = _run_upi(["/install", ccx_path])

    if code != 0:
        _log(f" Installation failed (code {code}): {output}")
        return False

    version = get_bundled_plugin_version()
    _log(f" Plugin installed successfully (v{version}).")
    return True


def uninstall_plugin(log_cb=None) -> bool:
    """
    Uninstall the plugin via UPI.
    Returns True on success.
    """
    def _log(msg: str) -> None:
        if log_cb:
            log_cb(msg)

    if not is_upi_available():
        _log(" Adobe UPI not found.")
        return False

    _log(f" Uninstalling '{PLUGIN_NAME}'...")
    code, output = _run_upi(["/remove", PLUGIN_NAME])

    if code != 0:
        _log(f" Uninstall failed (code {code}): {output}")
        return False

    _log(" Plugin uninstalled.")
    return True
