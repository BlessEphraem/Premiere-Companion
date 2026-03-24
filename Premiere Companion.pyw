# Premiere Companion.pyw
import sys
import os
import ctypes
import json

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{os.path.abspath(__file__)}"', None, 1)
    sys.exit()

os.chdir(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from GUI.main_window import MainWindow
from Core.paths import get_data_path, get_base_path

def get_theme_colors():
    """Charge les couleurs de l'utilisateur depuis le JSON ou utilise celles par défaut"""
    defaults = {"accent": "#FF1796", "bg": "#09090b"}
    theme_path = get_data_path("theme.json")
    
    if os.path.exists(theme_path):
        try:
            with open(theme_path, "r", encoding="utf-8") as f:
                defaults.update(json.load(f))
        except Exception:
            pass
    return defaults

def main():
    myappid = 'ephraem.premierecompanion'
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # --- CHARGEMENT DE L'ICÔNE ---
    # Recherche l'icône dans Icons/icon.ico (relativement au dossier de base)
    base_dir = get_base_path()
    icon_path = os.path.join(base_dir, "Icons", "icon.ico")
    
    # Fallback pour PyInstaller (si Icons n'est pas trouvé)
    if not os.path.exists(icon_path):
        icon_path = os.path.join(base_dir, "icon.ico")

    app_icon = None
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)

    # 1. Récupération des couleurs
    colors = get_theme_colors()
    ACCENT = colors.get("accent", "#FF1796")
    BG = colors.get("bg", "#09090b")

    # 2. Nettoyage silencieux de l'ancien fichier .qss s'il existe
    old_style_path = get_data_path("style.qss")
    if os.path.exists(old_style_path):
        try:
            os.remove(old_style_path)
        except:
            pass

    # 3. Le QSS dynamique complet
    dynamic_qss = f"""
    QMainWindow, QWidget {{ background-color: {BG}; color: #e4e4e7; font-family: "Inter", "Segoe UI", "-apple-system", "Helvetica Neue", sans-serif; font-size: 14px; }}
    QLabel {{ background-color: transparent; color: #e4e4e7; font-weight: 500; }}
    QLineEdit, QComboBox, QSpinBox {{ background-color: #18181b; color: #ffffff; border: 1px solid #27272a; border-radius: 8px; padding: 10px 14px; }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{ border: 1px solid {ACCENT}; background-color: #202024; }}
    QPushButton {{ background-color: #18181b; color: #fafafa; border: 1px solid #27272a; border-radius: 8px; padding: 10px 16px; font-weight: 600; font-size: 13px; }}
    QPushButton:hover {{ background-color: #27272a; border: 1px solid #3f3f46; }}
    QPushButton:pressed {{ background-color: #18181b; border: 1px solid {ACCENT}; color: {ACCENT}; }}
    QListWidget, QTextEdit, QScrollArea {{ background-color: {BG}; border: 1px solid #27272a; border-radius: 10px; padding: 6px; outline: none; color: #ffffff; font-size: 15px; font-weight: 600; }}
    QListWidget::item {{ background-color: #121214; border: 1px solid #18181b; border-radius: 8px; margin: 4px; padding-left: 15px; min-height: 40px; }}
    QListWidget::item:hover {{ background-color: #18181b; border: 1px solid #27272a; }}
    QListWidget::item:selected {{ background-color: #1e293b; border: 1px solid {ACCENT}; color: #ffffff; }}
    QScrollBar:vertical {{ background: transparent; width: 8px; margin: 2px; border-radius: 4px; }}
    QScrollBar::handle:vertical {{ background: #3f3f46; min-height: 30px; border-radius: 4px; }}
    QScrollBar::handle:vertical:hover {{ background: #52525b; }}
    QFrame#separatorLine {{ background-color: #27272a; max-height: 1px; }}
    QLabel#PageTitle {{ font-size: 22px; font-weight: bold; color: #ffffff; }}
    QFrame#CardFrame {{ background-color: #121214; border: 1px solid #27272a; border-radius: 8px; }}
    QLabel#CardLabel {{ font-weight: bold; font-size: 14px; border: none; }}
    QLabel#CardLabelBold {{ font-size: 16px; font-weight: bold; border: none; }}
    QLabel#CardLabelSubtle {{ color: #a1a1aa; border: none; }}
    QLabel#WarningLabel {{ color: #ffaa00; font-style: italic; font-size: 12px; }}
    QCheckBox#SubtleCheckbox {{ border: none; color: #a1a1aa; font-weight: bold; }}
    QScrollArea#TransparentScroll, QWidget#TransparentContainer, QWidget#effectItem, QWidget#FloatingSearchBar {{ background: transparent; border: none; }}
    QPushButton#PrimaryButton {{ background-color: #3b82f6; border: none; font-size: 16px; padding: 10px; font-weight: bold; }}
    QPushButton#PrimaryButton:hover {{ background-color: #2563eb; }}
    QPushButton#AccentButton {{ background-color: #aa00ff; border: none; color: white; font-size: 14px; font-weight: bold; padding: 10px; }}
    QPushButton#AccentButton:hover {{ background-color: #9000d8; }}
    QPushButton#NavButton[active="true"] {{ background-color: {ACCENT}; border: none; font-weight: bold; }}
    QPushButton#ToggleQA[qa_state="enabled"] {{ background-color: #55ff55; color: black; font-weight: bold; padding: 5px; border: none; }}
    QPushButton#ToggleQA[qa_state="disabled"] {{ background-color: #ff5555; color: white; font-weight: bold; padding: 5px; border: none; }}
    QLabel#EffectTag {{ font-weight: bold; font-size: 14px; margin-right: 5px; }}
    QLabel#EffectTag[type="TagVideo"]      {{ color: #ff5555; }}
    QLabel#EffectTag[type="TagAudio"]      {{ color: #55ff55; }}
    QLabel#EffectTag[type="TagTransition"] {{ color: #55ccff; }}
    QLabel#EffectTag[type="TagPreset"]     {{ color: #ffffff; }}
    QLabel#EffectTag[type="TagRecent"]     {{ color: #ffaa00; }}
    QLabel#EffectTag[type="unknown"]       {{ color: #3b82f6; }}
    QLabel#StatusLabel[connected="true"] {{ color: #55ff55; font-weight: bold; }}
    QLabel#StatusLabel[connected="false"] {{ color: #ff5555; font-weight: bold; }}
    QLabel#CoordLabel[state="undefined"] {{ color: #ffaa00; font-weight: bold; font-size: 14px; }}
    QLabel#CoordLabel[state="saved"] {{ color: #55ff55; font-weight: bold; font-size: 14px; }}
    QFrame#SearchBarContainer {{ background-color: rgba(30, 30, 30, 240); border: 1px solid #555555; border-radius: 12px; }}
    QListWidget#SearchList {{ background-color: transparent; border: none; color: #dddddd; font-size: 14px; outline: none; }}
    QListWidget#SearchList::item:selected {{ background-color: #005577; color: white; border: 1px solid #0077aa; }}
    QLineEdit#MainSearchBar {{ background-color: #18181b; color: #ffffff; border-radius: 8px; padding: 10px 14px; font-weight: bold; }}
    QLineEdit#MainSearchBar:focus {{ background-color: #202024; }}
    QLineEdit#MainSearchBar[filterType="All"] {{ border: 2px solid #3b82f6; }}
    QLineEdit#MainSearchBar[filterType="FxVideo"] {{ border: 2px solid #ff5555; }}
    QLineEdit#MainSearchBar[filterType="FxAudio"] {{ border: 2px solid #55ff55; }}
    QLineEdit#MainSearchBar[filterType="Transition"] {{ border: 2px solid #55ccff; }}
    QLineEdit#MainSearchBar[filterType="Preset"] {{ border: 2px solid #ffffff; }}
    QLineEdit#SearchInput {{ background-color: rgba(15, 15, 15, 200); color: #ffffff; border-radius: 8px; padding: 12px 15px; font-size: 16px; font-weight: bold; }}
    QLineEdit#SearchInput[filterType="All"] {{ border: 1px solid #3b82f6; }}
    QLineEdit#SearchInput[filterType="FxVideo"] {{ border: 1px solid #ff5555; }}
    QLineEdit#SearchInput[filterType="FxAudio"] {{ border: 1px solid #55ff55; }}
    QLineEdit#SearchInput[filterType="Transition"] {{ border: 1px solid #55ccff; }}
    QLineEdit#SearchInput[filterType="Preset"] {{ border: 1px solid #ffffff; }}
    QLineEdit#SearchInput[mode="options"] {{ border: 2px solid #55ccff; background-color: rgba(15, 15, 15, 200); color: white; }}
    QLabel#SearchResultName {{ color: #e4e4e7; font-size: 15px; font-weight: bold; }}
    QLabel#RegexRuleText {{ color: #e4e4e7; font-size: 14px; background: transparent; }}
    """

    app.setStyleSheet(dynamic_qss)

    window = MainWindow()
    
    # Applique aussi l'icône spécifiquement à la fenêtre principale par sécurité
    if app_icon:
        window.setWindowIcon(app_icon)
        
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()