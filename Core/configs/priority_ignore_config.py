# Core/configs/priority_ignore_config.py

DEFAULT_PRIORITY_IGNORE_CONFIG = {
    "group_priority": {   # rank 1 = displayed first in search results
        "FX.V":   1,
        "FX.A":   2,
        "TR.V":   3,
        "PRST":   4,
        "CMD":    5,
    },
    "priority": [],   # list of {"match_name": str, "value": int (1–999)}
    "ignore":   []    # list of matchNames — hidden from all lists and search
}
