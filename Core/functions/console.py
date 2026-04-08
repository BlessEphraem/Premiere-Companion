# Core/functions/console.py
# Helper for console output with theme integration

from Core.theme_qss import THEME_USER_COLORS

def log_to_console(main_window, message, color_key="info"):
    """
    Appends a message to the UI console with a specific theme color.
    
    :param main_window: The EffectsPage instance.
    :param message: String to display.
    :param color_key: Key in THEME_USER_COLORS (e.g., 'success', 'error', 'info').
    """
    color = THEME_USER_COLORS[color_key]
    if hasattr(main_window, "append_log"):
        main_window.append_log(message, color)
