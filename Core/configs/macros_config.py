# Core/configs/macros_config.py
import json
import os
from Core.paths import get_data_path

DEFAULT_MACROS_CONFIG = {
    "macros": []
}

def load_macros_config():
    path = get_data_path("macros_config.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_MACROS_CONFIG.copy()

def save_macros_config(config):
    path = get_data_path("macros_config.json")
    os.makedirs(get_data_path(), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
