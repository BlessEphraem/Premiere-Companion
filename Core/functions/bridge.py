# Modules/bridge.py
# Bridge module for Premiere Pro communication and version management
import os
import json
from Core.paths import get_data_path

_detected_version = ""
_detected_name = ""


def get_premiere_version():
    return _detected_version


def get_premiere_name():
    return _detected_name


def set_premiere_version(version, name=""):
    global _detected_version, _detected_name
    _detected_version = version
    _detected_name = name


def normalize_version(version):
    if not version:
        return None
    parts = version.split(".")
    if len(parts) >= 1 and parts[0].isdigit():
        return f"{parts[0]}.0"
    return None


def get_available_versions():
    docs_path = os.path.expanduser(r"~\Documents\Adobe\Premiere Pro")
    if not os.path.exists(docs_path):
        return []
    try:
        versions = [f for f in os.listdir(docs_path)
                    if os.path.isdir(os.path.join(docs_path, f)) and f[0].isdigit()]
        versions.sort(key=lambda x: os.path.getmtime(os.path.join(docs_path, x)), reverse=True)
        return versions
    except:
        return []


def load_quick_apply_config():
    qa_path = get_data_path("quickApply_config.json")
    if os.path.exists(qa_path):
        try:
            with open(qa_path, "r") as f:
                return json.load(f)
        except:
            pass
    return {"quick_apply_enabled": False, "keep_on_mouse": False}


def save_quick_apply_config(data):
    qa_path = get_data_path("quickApply_config.json")
    os.makedirs(get_data_path(), exist_ok=True)
    with open(qa_path, "w") as f:
        json.dump(data, f)


def request_premiere_version():
    from Core.functions.server import send_to_plugin
    send_to_plugin({"action": "get_premiere_version"})
