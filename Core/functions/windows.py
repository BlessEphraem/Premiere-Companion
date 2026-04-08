# Core/windows.py
# Window Manager - Centralized window configuration and creation

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog
from GUI.Pages.theme_page import ThemePage
from GUI.Pages.searchbar_page import SearchBarPage
from GUI.Pages.quickApply_page import QuickApplyWizard
from GUI.Pages.premiere_page import PremierePage
from GUI.Pages.regex_page import RegexPage
from GUI.Pages.betterMotion_page import BetterMotionPage
from GUI.Pages.premiereKeybinds_page import PremiereKeybindsPage
from GUI.Pages.customHotkey_page import CustomHotkeyPage
from GUI.Pages.priorityIgnore_page import PriorityIgnorePage
from GUI.Pages.commands_page import CommandsPage
from GUI.Pages.macro_editor_page import MacroEditorPage

WINDOW_SIZES = {
    "main": {"width": 540, "height": 785},
    "main_min": {"width": 540, "height": 540},
    "theme": {"width": "auto", "height": "auto"},
    "searchbar": {"width": "auto", "height": "auto"},
    "quick_apply": {"width": "auto", "height": "auto"},
    "premiere": {"width": "auto", "height": "auto"},
    "regex": {"width": 540, "height": 400},
    "better_motion": {"width": "auto", "height": "auto"},
    "premiere_keybinds": {"width": 540, "height": 400},
    "custom_hotkey": {"width": 540, "height": 500},
    "priority_ignore": {"width": 540, "height": 700},
    "commands": {"width": "auto", "height": "auto"},
    "macro_editor": {"width": 540, "height": 600},
}


def get_window_config(window_type):
    return WINDOW_SIZES.get(window_type, {"width": 540, "height": 540})


def apply_window_config(window, window_type, title=None):
    config = get_window_config(window_type)
    width = config["width"]
    height = config["height"]
    
    if width != "auto":
        window.setMinimumSize(width, 0)
    else:
        window.setMinimumSize(0, 0)
        window.adjustSize()
        window.setMinimumSize(window.sizeHint())
    
    if height == "auto":
        window.adjustSize()
        window.setMinimumSize(window.sizeHint())
    else:
        window.resize(width, height)
    
    if title:
        window.setWindowTitle(title)
    
    return window


def create_window(window_type, parent, modal=True):
    
    if window_type == "theme":
        window = ThemePage(parent)
        window.setParent(parent)
        apply_window_config(window, "theme", "Theme Configuration")
        window.setWindowModality(Qt.WindowModality.NonModal)
        
    elif window_type == "searchbar":
        window = SearchBarPage(parent)
        window.setParent(parent)
        apply_window_config(window, "searchbar", "SearchBar Configuration")
        
    elif window_type == "quick_apply":
        window = QuickApplyWizard(parent)
        window.setParent(parent)
        apply_window_config(window, "quick_apply", "Configuration: Quick Apply for Presets")
        
    elif window_type == "premiere":
        from PyQt6.QtWidgets import QVBoxLayout
        dialog = QDialog(parent)
        dialog.setWindowTitle("Premiere Pro")
        apply_window_config(dialog, "premiere")
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        layout = QVBoxLayout(dialog)
        page = PremierePage(parent)
        layout.addWidget(page)
        return dialog
        
    elif window_type == "regex":
        from PyQt6.QtWidgets import QVBoxLayout
        dialog = QDialog(parent)
        dialog.setWindowTitle("RegEx Rules")
        apply_window_config(dialog, "regex")
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        layout = QVBoxLayout(dialog)
        page = RegexPage(parent)
        layout.addWidget(page)
        return dialog
    
    elif window_type == "better_motion":
        window = BetterMotionPage(parent)
        window.setParent(parent)
        apply_window_config(window, "better_motion", "Configuration: Better Motion")
        return window
    
    elif window_type == "premiere_keybinds":
        from PyQt6.QtWidgets import QVBoxLayout
        dialog = QDialog(parent)
        dialog.setWindowTitle("Premiere Keybinds")
        apply_window_config(dialog, "premiere_keybinds")
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        layout = QVBoxLayout(dialog)
        page = PremiereKeybindsPage(parent)
        layout.addWidget(page)
        return dialog
    
    elif window_type == "custom_hotkey":
        from PyQt6.QtWidgets import QVBoxLayout
        dialog = QDialog(parent)
        dialog.setWindowTitle("Custom Hotkeys")
        apply_window_config(dialog, "custom_hotkey")
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        layout = QVBoxLayout(dialog)
        page = CustomHotkeyPage(parent)
        layout.addWidget(page)
        return dialog

    elif window_type == "priority_ignore":
        window = PriorityIgnorePage(parent)
        window.setParent(parent)
        apply_window_config(window, "priority_ignore", "Priority & Ignore")
        return window

    elif window_type == "commands":
        window = CommandsPage(parent)
        window.setParent(parent)
        apply_window_config(window, "commands", "Commands Configuration")
        return window

    elif window_type == "macro_editor":
        window = MacroEditorPage(parent)
        window.setParent(parent)
        apply_window_config(window, "macro_editor", "Macro Editor")
        return window

    else:
        raise ValueError(f"Unknown window type: {window_type}")
    
    return window
