from Core.configs.search_config import SEARCHBAR_DEFAULTS, SEARCH_TIMER_DELAY
# Core/search.py
# Centralized search and filter configuration

import os
import json
from Core.configs.labels_config import get_labels
from Core.paths import get_data_path

_filter_modes_cache = None

def _get_filter_modes():
    global _filter_modes_cache
    if _filter_modes_cache is None:
        labels = get_labels()
        _filter_modes_cache = [{"name": "All", "type": "All"}]
        for type_code, data in labels.items():
            if type_code.startswith("CMD."):
                continue
            _filter_modes_cache.append({"name": data["label"], "type": type_code})
    return _filter_modes_cache

def invalidate_filter_modes_cache():
    global _filter_modes_cache
    _filter_modes_cache = None

def get_filter_modes():
    return _get_filter_modes()

FILTER_MODES = _get_filter_modes()

def cycle_filter(current_idx, direction):
    return (current_idx + direction) % len(FILTER_MODES)





_history_file = None

def _get_history_path():
    global _history_file
    if _history_file is None:
        _history_file = get_data_path("search_history.json")
    return _history_file

def load_search_history():
    """Load search history with migration from old format (array) to new format (object)."""
    history_path = _get_history_path()
    
    if os.path.exists(history_path):
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if isinstance(data, list):
                return {"last_used": None, "history": data, "dynamic_data": {}}
            return {
                "last_used": data.get("last_used"),
                "history": data.get("history", []),
                "dynamic_data": data.get("dynamic_data", {}),
            }
        except Exception:
            pass
    
    return {"last_used": None, "history": []}

def save_last_used(match_name, effect_type, display_name, custom_data=None):
    """Save last used item to search_history.json and update history list."""
    history_path = _get_history_path()
    data = load_search_history()

    # Update last_used
    data["last_used"] = {
        "match_name": match_name,
        "type": effect_type,
        "display_name": display_name
    }

    # Update history list
    history = data.get("history", [])
    if match_name in history:
        history.remove(match_name)
    history.insert(0, match_name)

    # Respect max_recent from config
    config = load_searchbar_config()
    max_recent = config.get("max_recent", 5)
    data["history"] = history[:max_recent]

    # Persist custom_data for dynamic commands (e.g. "CMD.BM.opacity.dynamic" → "0")
    if custom_data is not None:
        dd = data.get("dynamic_data", {})
        dd[match_name] = {"custom_data": custom_data, "displayName": display_name, "type": effect_type}
        data["dynamic_data"] = dd

    os.makedirs(os.path.dirname(history_path), exist_ok=True)
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def save_history_list(history_items):
    """Save history list to search_history.json (preserves last_used)."""
    history_path = _get_history_path()
    data = load_search_history()
    data["history"] = history_items
    os.makedirs(os.path.dirname(history_path), exist_ok=True)
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def get_last_used():
    """Get last_used from search_history.json."""
    return load_search_history().get("last_used")

def load_searchbar_config():
    """Load searchbar config from searchbar_config.json."""
    config_path = get_data_path("searchbar_config.json")
    config = SEARCHBAR_DEFAULTS.copy()
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config.update(json.load(f))
        except Exception:
            pass
    return config

def load_commands_config():
    """Load commands/keywords config from commands_config.json."""
    from Core.configs.commands_config import DEFAULT_COMMANDS_CONFIG
    config_path = get_data_path("commands_config.json")
    config = {k: v for k, v in DEFAULT_COMMANDS_CONFIG.items()}
    config["keywords"] = dict(DEFAULT_COMMANDS_CONFIG["keywords"])
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            config["keywords_enabled"] = data.get("keywords_enabled", config["keywords_enabled"])
            if "keywords" in data:
                config["keywords"].update(data["keywords"])
        except Exception:
            pass
    return config

def load_priority_ignore_config():
    """
    Load priority/ignore config from priority_ignore_config.json.

    Handles migration from old format where 'priority' was a list of strings
    instead of a list of {"match_name": str, "value": int} dicts.
    """
    from Core.configs.priority_ignore_config import DEFAULT_PRIORITY_IGNORE_CONFIG
    config_path = get_data_path("priority_ignore_config.json")
    config = {
        "group_priority": dict(DEFAULT_PRIORITY_IGNORE_CONFIG["group_priority"]),
        "priority": [],
        "ignore": [],
    }
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "group_priority" in data:
                config["group_priority"].update(data["group_priority"])

            raw_priority = data.get("priority", [])
            # Migration: old format was [str], new format is [{"match_name": str, "value": int}]
            if raw_priority and isinstance(raw_priority[0], str):
                config["priority"] = [{"match_name": mn, "value": 1} for mn in raw_priority]
            else:
                config["priority"] = raw_priority

            config["ignore"] = data.get("ignore", [])
        except Exception:
            pass
    return config

def parse_search_command(query, commands_config):
    """
    Parse a command prefix from a search query.
    Returns (type_override, actual_query).
    type_override is None if no prefix matched.
    """
    if not commands_config.get("keywords_enabled", True):
        return None, query

    if not query.startswith("/"):
        return None, query

    keywords = commands_config.get("keywords", {})
    after_slash = query[1:]

    # Sort by keyword length descending so "QA" is matched before "Q"
    sorted_kw = sorted(keywords.items(), key=lambda x: len(x[1]), reverse=True)

    for type_code, kw_char in sorted_kw:
        if after_slash.lower().startswith(kw_char.lower()):
            rest = after_slash[len(kw_char):]
            if rest == "" or rest.startswith(" "):
                return type_code, rest.lstrip(" ")

    return None, query
