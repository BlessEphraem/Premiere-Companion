# Core/version.py
# APP_VERSION is injected at build time by build_app.bat into _build_version.py.
# In development (no build step), it falls back to "dev".
# PLUGIN_VERSION is never stored here — read live from Plugin/manifest.json.

try:
    from Core._build_version import APP_VERSION  # type: ignore
except ImportError:
    APP_VERSION = "dev"

GITHUB_REPO = "BlessEphraem/Premiere-Companion"
GITHUB_RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases"
