# Core/labels.py
import json
import os
from Core.paths import get_data_path

_DEFAULT_LABELS = {
    "FX.V": {"label": "FX.V", "display": "[FX.V]", "color": "error"},
    "FX.A": {"label": "FX.A", "display": "[FX.A]", "color": "success"},
    "TR.V": {"label": "TR.V", "display": "[TR.V]", "color": "info"},
    "PRST": {"label": "PRST", "display": "[PRST]", "color": "white"},
    "CMD":  {"label": "CMD",  "display": "[CMD]",  "color": "warning"},
    "CMD.QA": {"label": "CMD.QA", "display": "[CMD.QA]", "color": "warning"},
    "CMD.BM": {"label": "CMD.BM", "display": "[CMD.BM]", "color": "warning"},
    "CMD.MA": {"label": "CMD.MA", "display": "[CMD.MA]", "color": "warning"},
}

def _ensure_labels_file():
    path = get_data_path("labels.json")
    if not os.path.exists(path):
        os.makedirs(get_data_path(), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"types": _DEFAULT_LABELS}, f, indent=4)
    else:
        # Merge any missing default keys into existing file
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            existing = data.get("types", {})
            updated = False
            for key, val in _DEFAULT_LABELS.items():
                if key not in existing:
                    existing[key] = val
                    updated = True
            if updated:
                data["types"] = existing
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
        except Exception:
            pass

def get_labels():
    _ensure_labels_file()
    path = get_data_path("labels.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("types", _DEFAULT_LABELS)
    except:
        return _DEFAULT_LABELS

def get_type_codes():
    return list(get_labels().keys())

def get_display_label(type_code):
    return get_labels().get(type_code, {}).get("display", f"[{type_code}]")

def get_color_key(type_code):
    return get_labels().get(type_code, {}).get("color", "primary")

def is_video(type_code):
    return "FX.V" in type_code and "TR.V" not in type_code

def is_audio(type_code):
    return "FX.A" in type_code and "TR.V" not in type_code

def is_transition(type_code):
    return "TR.V" in type_code

def is_preset(type_code):
    return "PRST" in type_code

def is_command(type_code):
    return type_code == "CMD" or type_code.startswith("CMD.")
