# Core/configs/betterMotion_config.py

DEFAULT_BM_CONFIG = {
    "enabled": False,
    "live_motion": False,
    "better_transform": {"key": "", "vk": 0},
    "position": {
        "adjust": "",
        "reset": {"key": "", "vk": 0},
        "x_add": {"key": "", "amount": 10},
        "x_sub": {"key": "", "amount": -10},
        "y_add": {"key": "", "amount": 10},
        "y_sub": {"key": "", "amount": -10}
    },
    "scale": {
        "adjust": "",
        "reset": {"key": "", "vk": 0},
        "add": {"key": "", "amount": 10},
        "sub": {"key": "", "amount": -10},
        "axis": "vertical", "invert": False
    },
    "rotation": {
        "adjust": "",
        "reset": {"key": "", "vk": 0},
        "add": {"key": "", "amount": 15},
        "sub": {"key": "", "amount": -15},
        "axis": "horizontal", "invert": False
    },
    "opacity": {
        "adjust": "",
        "reset": {"key": "", "vk": 0},
        "add": {"key": "", "amount": 10},
        "sub": {"key": "", "amount": -10},
        "axis": "vertical", "invert": False
    }
}
