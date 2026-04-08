# Core/keybinds.py
# Centralized default keybinds configuration

DEFAULT_KEYBINDS = {
    "Window > Timelines": "Shift+3",
    "Window > Effect": "Shift+2",
    "Search Find Box": "Shift+F",
}

# "Run Search Bar" is a Companion-level global hotkey (registered via
# RegisterHotKey), NOT a Premiere shortcut.  It lives separately in
# keybinds.json under its own key and is configured in keymaps_page, not in
# premiereKeybinds_page, to prevent accidental global key stealing.
DEFAULT_SEARCH_BAR_KEY = "Ctrl+Space"