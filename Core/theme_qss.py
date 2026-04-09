# Core/theme_qss.py
# Centralized theme configuration and QSS generator
import json
import os
from Core.paths import get_data_path

THEME_USER_COLORS = {
    # -- Non-editable / derived --
    "app_title":      "Premiere Companion",
    "text_white":     "#ffffff",
    "text_black":     "#000000",
    "btn_text":       "#fafafa",
    "hover_primary":  "#2563eb",
    "hover_accent":   "#9000d8",
    "hover_yellow":   "#ca8a04",
    "icon_nav":       "rgba(255, 255, 255, 0.5)",
    "icon_accent":    "#FF1796",
    "icon_warning":   "#ffaa00",

    # -- Editable (schema-driven) --
    "accent":           "#FF1796",
    "bg":               "#09090b",
    "btn_bg":           "#18181b",
    "input_bg":         "#18181b",
    "list_bg":          "#18181b",
    "console_bg":       "#18181b",
    "card_bg":          "none",
    "hover":            "#27272a",
    "text_main":        "#e4e4e7",
    "text_subtle":      "#a1a1aa",
    "info_text":        "#a1a1aa",
    "success":          "#55ff55",
    "label_audio":      "#55ff55",
    "error":            "#ff5555",
    "label_video":      "#ff5555",
    "info":             "#55ccff",
    "label_transition": "#55ccff",
    "warning":          "#ffaa00",
    "btn_accent_1":     "#3b82f6",
    "btn_accent_2":     "#aa00ff",
    "btn_accent_3":     "#ffc400",
    "icon_color":       "#e4e4e7",
    "font_family":      "Satoshi",
    "font_weight":      "Black",
}

QSS_CONSTANTS = {
    "border_none": "border: none;",
    "outline_none": "outline: none;",
    "bg_transparent": "background: transparent;",
    "bg_transparent_important": "background: transparent !important;",
}

THEME_SCHEMA = [
    ("accent",            "Accent Color",               "#FF1796"),
    ("bg",                "Main Background",            "#09090b"),
    ("btn_bg",            "Buttons Background",         "#18181b"),
    ("input_bg",          "InputBox Background",        "#18181b"),
    ("list_bg",           "Lists Background",           "#18181b"),
    ("console_bg",        "Console Background",         "#18181b"),
    ("card_bg",           "Card Background",            "none"),
    ("hover",             "Hover Color",                "#27272a"),
    ("text_main",         "Main Text Color",            "#e4e4e7"),
    ("text_subtle",       "Subtle Text Color",          "#a1a1aa"),
    ("info_text",         "Info Text Color",            "#a1a1aa"),
    ("success",           "Success Color",              "#55ff55"),
    ("label_audio",       "Label Audio",                "#55ff55"),
    ("error",             "Error Color",                "#ff5555"),
    ("label_video",       "Label Video",                "#ff5555"),
    ("info",              "Info Color",                 "#55ccff"),
    ("label_transition",  "Label Transition",           "#55ccff"),
    ("warning",           "Warning Color",              "#ffaa00"),
    ("btn_accent_1",      "Button Accent Background 1", "#3b82f6"),
    ("btn_accent_2",      "Button Accent Background 2", "#aa00ff"),
    ("btn_accent_3",      "Button Accent Background 3", "#ffc400"),
    ("icon_color",        "Icon Color",                 "#e4e4e7"),
    ("font_family",       "Font",                       "Satoshi"),
    ("font_weight",       "Font Weight",                "Black"),
]

THEME_SCHEMA_SECTIONS = [
    ("Core", [
        ("accent",  "Accent Color",   "#FF1796"),
        ("bg",      "Main Background","#09090b"),
        ("hover",   "Hover Color",    "#27272a"),
    ]),
    ("Backgrounds", [
        ("btn_bg",     "Buttons Background",  "#18181b"),
        ("input_bg",   "InputBox Background", "#18181b"),
        ("list_bg",    "Lists Background",    "#18181b"),
        ("console_bg", "Console Background",  "#18181b"),
        ("card_bg",    "Card Background",     "none"),
    ]),
    ("Text", [
        ("text_main",   "Main Text Color",   "#e4e4e7"),
        ("text_subtle", "Subtle Text Color", "#a1a1aa"),
        ("info_text",   "Info Text Color",   "#a1a1aa"),
    ]),
    ("Status Colors", [
        ("success", "Success Color", "#55ff55"),
        ("error",   "Error Color",   "#ff5555"),
        ("info",    "Info Color",    "#55ccff"),
        ("warning", "Warning Color", "#ffaa00"),
    ]),
    ("Labels", [
        ("label_audio",      "Label Audio",      "#55ff55"),
        ("label_video",      "Label Video",      "#ff5555"),
        ("label_transition", "Label Transition", "#55ccff"),
    ]),
    ("Buttons", [
        ("btn_accent_1", "Button Accent Background 1", "#3b82f6"),
        ("btn_accent_2", "Button Accent Background 2", "#aa00ff"),
        ("btn_accent_3", "Button Accent Background 3", "#ffc400"),
    ]),
    ("Icons", [
        ("icon_color", "Icon Color", "#e4e4e7"),
    ]),
    ("Typography", [
        ("font_family", "Font",        "Satoshi"),
        ("font_weight", "Font Weight", "Black"),
    ]),
]

THEME_TYPOGRAPHY = {
    "font_list": 15,
    "font_base": 14,
    "font_title": 44,
    "font_button": 14,
    "font_card_label": 14,
    "font_card_label_bold": 16,
    "font_warning": 12,
    "font_action_btn": 16,
    "font_search_input": 16,
    "font_search_result": 15,
    "font_label_bold": 14,
    "font_coord": 14,
    "font_error": 11,
    "font_splash_title": 20,
    "font_splash_status": 16,
    "font_splash_label": 18,
    "font_nav_title": 24,
}

THEME_SPACING = {
    "spacing_page": 6,
    "spacing_element": 6,
    "margin_none": 0,
    "padding_card": 0,
    "padding_container": 15,
    "padding_small": 10,
    "padding_tiny": 5,
    "spacing_tight": 2,
    "padding_splash": 16,
    "padding_splash_inner": 20,
    "icon_small": 40,
    "icon_medium": 20,
    "icon_large": 24,
    "icon_small_fixed": 16,
    "icon_button": 32,
    "width_button_small": 100,
    "width_button_medium": 120,
    "width_icon_button_fixed": 36,
    "padding_nav_button": 5,
    "padding_button": "10px 16px",
    "padding_list": "6px",
    "padding_list_item_left": 10,
    "padding_input": "10px 14px",
    "height_action_input": 40,
    "height_search_bar": 40,
    "radius_search_hover": "8px",
    "padding_search_input": "12px 15px",
    "radius_search_item": "6px",
    "radius_search_result": "12px",
    "padding_search_result_item": "8px",
    "margin_search_result_item": "2px",
    "width_input_keybind": 150,
    "width_input_port": 100,
    "height_console": 120,
    "height_list_item": 35,
    "margin_card": 0,
    "radius_small": "8px",
    "radius_medium": "10px",
    "radius_large": "12px",
    "margin_effect_tag_right": 5,
    "padding_info_label_vertical": 5,
    "padding_action_button": "10px",
    "splash_width": 400,
    "splash_height": 128,
    "splash_inner_width": 350,
    "splash_inner_height": 128,
    "splash_progress_height": 10,
}

def hex_to_rgba(hex_color, opacity=0.2):
    CSS_COLORS = {
        "black": "#000000", "white": "#ffffff", "red": "#ff0000", "green": "#008000",
        "blue": "#0000ff", "yellow": "#ffff00", "cyan": "#00ffff", "magenta": "#ff00ff",
        "gray": "#808080", "grey": "#808080", "orange": "#ffa500", "purple": "#800080",
        "pink": "#ffc0cb", "brown": "#a52a2a", "lime": "#00ff00", "navy": "#000080",
        "teal": "#008080", "olive": "#808000", "maroon": "#800000", "silver": "#c0c0c0",
    }
    hex_color = str(hex_color).strip().lower()
    if hex_color in CSS_COLORS:
        hex_color = CSS_COLORS[hex_color]
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6 or not all(c in '0123456789abcdefABCDEF' for c in hex_color):
        return f"rgba(128, 128, 128, {opacity})"
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {opacity})"

def normalize_color(color_value):
    if color_value and str(color_value).strip().lower() == "none":
        return "transparent"
    return str(color_value)

def generate_theme_qss(colors, loaded_font=None):
    full_colors = THEME_USER_COLORS.copy()
    if colors:
        full_colors.update(colors)
    c = full_colors

    ACCENT            = c.get("accent",           "#FF1796")
    BG                = normalize_color(c.get("bg",          "#09090b"))
    BTN_BG            = normalize_color(c.get("btn_bg",      "#18181b"))
    INPUT_BG          = normalize_color(c.get("input_bg",    "#18181b"))
    LIST_BG           = normalize_color(c.get("list_bg",     "#18181b"))
    CONSOLE_BG        = normalize_color(c.get("console_bg",  "#18181b"))
    CARD_BG           = normalize_color(c.get("card_bg",     "#121214"))
    HOVER             = c.get("hover",            "#27272a")
    TEXT              = c.get("text_main",        "#e4e4e7")
    TEXT_SUBTLE       = c.get("text_subtle",      "#a1a1aa")
    INFO_TEXT         = c.get("info_text",        "#a1a1aa")
    SUCCESS           = c.get("success",          "#55ff55")
    LABEL_AUDIO       = c.get("label_audio",      "#55ff55")
    ERROR             = c.get("error",            "#ff5555")
    LABEL_VIDEO       = c.get("label_video",      "#ff5555")
    INFO              = c.get("info",             "#55ccff")
    LABEL_TRANSITION  = c.get("label_transition", "#55ccff")
    WARNING           = c.get("warning",          "#ffaa00")
    BTN_ACCENT_1      = c.get("btn_accent_1",     "#3b82f6")
    BTN_ACCENT_2      = c.get("btn_accent_2",     "#aa00ff")
    BTN_ACCENT_3      = c.get("btn_accent_3",     "#ffc400")
    ICON_COLOR        = c.get("icon_color",       "#e4e4e7")
    TEXT_WHITE        = c.get("text_white",       "#ffffff")
    BTN_TEXT          = c.get("btn_text",         "#fafafa")
    HOVER_PRIMARY     = c.get("hover_primary",    "#2563eb")
    HOVER_ACCENT      = c.get("hover_accent",     "#9000d8")
    HOVER_YELLOW      = c.get("hover_yellow",     "#ca8a04")
    user_font         = c.get("font_family",      "Satoshi")
    font_weight       = c.get("font_weight",      "Black")

    if user_font == "Satoshi" and loaded_font:
        FONT_FAMILY = loaded_font
    elif user_font and user_font != "System Default":
        FONT_FAMILY = user_font
    else:
        FONT_FAMILY = "Inter, Segoe UI, -apple-system, Helvetica Neue, sans-serif"

    FILTER_BG_VIDEO      = hex_to_rgba(ERROR,   0.2)
    FILTER_BG_AUDIO      = hex_to_rgba(SUCCESS, 0.2)
    FILTER_BG_TRANSITION = hex_to_rgba(INFO,    0.2)
    FILTER_BG_PRESET     = "rgba(255, 255, 255, 0.15)"

    RS = THEME_SPACING["radius_small"]
    RM = THEME_SPACING["radius_medium"]
    RL = THEME_SPACING["radius_large"]
    BP = THEME_SPACING["padding_button"]
    IP = THEME_SPACING["padding_input"]
    LP = THEME_SPACING["padding_list"]
    SIP = THEME_SPACING["padding_search_input"]
    HLI = THEME_SPACING["height_list_item"]
    LIPL = THEME_SPACING["padding_list_item_left"]
    NBP = THEME_SPACING["padding_nav_button"]
    METR = THEME_SPACING["margin_effect_tag_right"]
    PIV = THEME_SPACING["padding_info_label_vertical"]
    ABP = THEME_SPACING["padding_action_button"]

    FB = THEME_TYPOGRAPHY["font_base"]
    FBT = THEME_TYPOGRAPHY["font_button"]
    FL = THEME_TYPOGRAPHY["font_list"]
    FT = THEME_TYPOGRAPHY["font_title"]
    FCL = THEME_TYPOGRAPHY["font_card_label"]
    FCLB = THEME_TYPOGRAPHY["font_card_label_bold"]
    FW = THEME_TYPOGRAPHY["font_warning"]
    FAB = THEME_TYPOGRAPHY["font_action_btn"]
    FSR = THEME_TYPOGRAPHY["font_search_result"]
    FLB = THEME_TYPOGRAPHY["font_label_bold"]
    FE = THEME_TYPOGRAPHY["font_error"]
    FNT = THEME_TYPOGRAPHY["font_nav_title"]

    BN = QSS_CONSTANTS["border_none"]
    ON = QSS_CONSTANTS["outline_none"]
    BGT = QSS_CONSTANTS["bg_transparent"]

    BG_LABEL_VIDEO      = hex_to_rgba(LABEL_VIDEO, 0.15)
    BG_LABEL_AUDIO      = hex_to_rgba(LABEL_AUDIO, 0.15)
    BG_LABEL_TRANSITION = hex_to_rgba(LABEL_TRANSITION, 0.15)
    BG_LABEL_PRESET     = hex_to_rgba(TEXT_WHITE, 0.15)
    BG_LABEL_COMMAND    = hex_to_rgba(WARNING, 0.15)
    BG_LABEL_UNKNOWN    = hex_to_rgba(BTN_ACCENT_1, 0.15)

    dynamic_qss = f"""
    * {{ {ON} }}
    QMainWindow, QWidget {{ background-color: {BG}; color: {TEXT}; font-family: "{FONT_FAMILY}", sans-serif; font-size: {FB}px; font-weight: {font_weight}; }}
    QLabel {{ background-color: transparent; color: {TEXT}; padding: 0; margin: 0; {BN} }}
    QLineEdit, QComboBox, QSpinBox {{ background-color: {INPUT_BG}; color: {TEXT_WHITE}; {BN} border-radius: {RS}; padding: {IP}; {ON} }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{ background-color: {HOVER}; {ON} }}
    QPushButton {{ background-color: {BTN_BG}; color: {BTN_TEXT}; {BN} border-radius: {RS}; padding: {BP}; font-size: {FBT}px; font-weight: bold; {ON} }}
    QPushButton:hover {{ background-color: {HOVER}; {ON} }}
    QPushButton:focus, QPushButton:pressed {{ background-color: {BTN_BG}; color: {TEXT}; {ON} {BN} }}
    QListWidget, QScrollArea {{ background-color: {LIST_BG}; color: {TEXT_WHITE}; {BN} border-radius: {RM}; padding: {LP}; font-size: {FL}px; {ON} }}
    QTextEdit {{ background-color: {CONSOLE_BG}; color: {TEXT_WHITE}; {BN} border-radius: {RM}; padding: {LP}; font-size: {FL}px; {ON} }}
    QListWidget::item {{ background-color: transparent; {BN} padding-left: {LIPL}px; min-height: {HLI}px; {ON} }}
    QListWidget::item:hover {{ background-color: {HOVER}; border-radius: {RS}; {ON} }}
    QListWidget::item:selected {{ background-color: {HOVER}; {BN} border-radius: {RS}; color: {TEXT_WHITE}; {ON} }}
    QScrollBar:vertical {{ background: transparent; width: 0px; margin: 0px; {BN} }}
    QScrollBar::handle:vertical {{ background: transparent; min-height: 0px; }}
    QScrollBar:horizontal {{ background: transparent; height: 0px; margin: 0px; {BN} }}
    QScrollBar::handle:horizontal {{ background: transparent; min-width: 0px; }}
    QLabel#PageTitle {{ font-size: {FT}px; color: {TEXT_WHITE}; padding: 0; margin: 0; }}
    QLabel#NavTitle {{ font-size: {FNT}px; color: {TEXT}; font-weight: bold; padding: 0; margin: 0; }}
    QPushButton#PageTitleBtn {{ {BGT} {BN} padding: 0; font-size: {FT}px; color: {TEXT_WHITE}; font-weight: bold; {ON} }}
    QPushButton#CardLabelBoldBtn {{ {BGT} {BN} padding: 0; font-size: {FCLB}px; font-weight: bold; color: {TEXT_WHITE}; {ON} }}
    QFrame#CardFrame {{ background-color: {CARD_BG}; {BN} border-radius: {RS}; }}
    QLabel#CardLabel {{ font-weight: bold; font-size: {FCL}px; {BN} padding: 0; margin: 0; }}
    QLabel#CardLabelBold {{ font-size: {FCLB}px; font-weight: bold; {BN} padding: 0; margin: 0; }}
    QLabel#CardLabelSubtle {{ color: {TEXT_SUBTLE}; {BN} padding: 0; margin: 0; }}
    QLabel#WarningLabel {{ color: {WARNING}; font-style: italic; font-size: {FW}px; padding: 0; margin: 0; }}
    QCheckBox#SubtleCheckbox {{ {BN} color: {TEXT_SUBTLE}; font-weight: bold; }}
    QScrollArea#TransparentScroll, QWidget#TransparentContainer, QWidget#effectItem {{ {BGT} {BN} }}
    QPushButton#PrimaryButton {{ background-color: {BTN_ACCENT_1}; {BN} font-size: {FAB}px; padding: {ABP}; font-weight: bold; {ON} }}
    QPushButton#PrimaryButton:hover {{ background-color: {HOVER_PRIMARY}; {ON} }}
    QPushButton#AccentButton {{ background-color: {BTN_ACCENT_2}; {BN} color: {TEXT_WHITE}; font-size: {FAB}px; font-weight: bold; padding: {ABP}; {ON} }}
    QPushButton#AccentButton:hover {{ background-color: {HOVER_ACCENT}; {ON} }}
    QPushButton#FetchEffectsBtn, QPushButton#ReloadRulesBtn {{ background-color: {BTN_ACCENT_3}; {BN} color: {TEXT_WHITE}; font-size: {FAB}px; font-weight: bold; padding: {ABP}; {ON} }}
    QPushButton#FetchEffectsBtn:hover, QPushButton#ReloadRulesBtn:hover {{ background-color: {HOVER_YELLOW}; {ON} }}
    QPushButton#ConsoleButton {{ background-color: {ACCENT}; {BN} color: {TEXT_WHITE}; font-size: {FAB}px; font-weight: bold; padding: {ABP}; {ON} }}
    QPushButton#NavButton {{ background-color: {BTN_BG}; {BN} {ON}}}
    QPushButton#NavButton[active="true"] {{ background-color: {ACCENT}; {BN} {ON} }}
    QPushButton#Toggle[qa_state="enabled"] {{ background-color: {SUCCESS}; color: black; font-weight: bold; padding: {NBP}px; {BN} {ON} }}
    QPushButton#Toggle[qa_state="disabled"] {{ background-color: {ERROR}; color: white; font-weight: bold; padding: {NBP}px; {BN} {ON} }}
    QLabel#EffectTag {{ font-weight: bold; font-size: 11px; margin-right: {METR}px; padding: 2px 4px; border-radius: 4px; }}
    QLabel#EffectTag[type="TagVideo"] {{ color: {LABEL_VIDEO}; border: 1px solid {LABEL_VIDEO}; background-color: {BG_LABEL_VIDEO}; }}
    QLabel#EffectTag[type="TagAudio"] {{ color: {LABEL_AUDIO}; border: 1px solid {LABEL_AUDIO}; background-color: {BG_LABEL_AUDIO}; }}
    QLabel#EffectTag[type="TagTransition"] {{ color: {LABEL_TRANSITION}; border: 1px solid {LABEL_TRANSITION}; background-color: {BG_LABEL_TRANSITION}; }}
    QLabel#EffectTag[type="TagPreset"] {{ color: {TEXT_WHITE}; border: 1px solid {TEXT_WHITE}; background-color: {BG_LABEL_PRESET}; }}
    QLabel#EffectTag[type="TagRecent"], QLabel#EffectTag[type="TagLastUsed"], QLabel#EffectTag[type="TagCommand"] {{ color: {WARNING}; border: 1px solid {WARNING}; background-color: {BG_LABEL_COMMAND}; }}
    QLabel#EffectTag[type="unknown"] {{ color: {BTN_ACCENT_1}; border: 1px solid {BTN_ACCENT_1}; background-color: {BG_LABEL_UNKNOWN}; }}
    QLabel#StatusLabel[connected="true"] {{ color: {SUCCESS}; font-weight: bold; }}
    QLabel#StatusLabel[connected="false"] {{ color: {ERROR}; font-weight: bold; }}
    QLabel#StatusLabel {{ color: {TEXT_SUBTLE}; font-weight: bold; }}
    QLabel#CoordLabel[state="undefined"] {{ color: {WARNING}; font-weight: bold; font-size: {FLB}px; }}
    QLabel#CoordLabel[state="saved"] {{ color: {SUCCESS}; font-weight: bold; font-size: {FLB}px; }}
    QFrame#SearchBarContainer {{ background-color: {LIST_BG}; {BN} border-radius: {RL}; }}
    QListWidget#SearchList {{ background-color: {LIST_BG}; {BN} border-radius: {RS}; color: {TEXT_WHITE}; font-size: {FLB}px; {ON} }}
    QLineEdit#MainSearchBar {{ background-color: {INPUT_BG}; color: {TEXT_WHITE}; border-radius: {RS}; padding: {IP}; font-weight: bold; {BN} {ON} }}
    QLineEdit#MainSearchBar:focus {{ background-color: {HOVER}; {ON} }}
    QLineEdit#MainSearchBar[filterType="FX.V"] {{ background-color: {FILTER_BG_VIDEO}; }}
    QLineEdit#MainSearchBar[filterType="FX.A"] {{ background-color: {FILTER_BG_AUDIO}; }}
    QLineEdit#MainSearchBar[filterType="TR.V"] {{ background-color: {FILTER_BG_TRANSITION}; }}
    QLineEdit#MainSearchBar[filterType="PRST"] {{ background-color: {FILTER_BG_PRESET}; }}
    QLineEdit#SearchInput {{ background-color: {BG}; color: {TEXT_WHITE}; {BN} border-radius: {RS}; padding: {SIP}; font-size: {FAB}px; font-weight: bold; {ON} }}
    QLabel#SearchResultName, QLabel#effectName {{ color: {TEXT_WHITE}; font-size: {FSR}px; font-weight: bold; padding: 0; margin: 0; }}
    QLabel#RegexRuleText {{ color: {TEXT_WHITE}; font-size: {FCL}px; {BGT} padding: 0; margin: 0; }}
    QLabel#SectionTitle {{ font-size: {FAB}px; font-weight: bold; margin-top: 20px; color: {TEXT_WHITE}; }}
    QLabel#SectionTitleFirst {{ font-size: {FAB}px; font-weight: bold; margin-top: 10px; color: {TEXT_WHITE}; }}
    QLabel#ThemeSectionTitle {{ color: {TEXT_SUBTLE}; font-size: 11px; font-weight: bold; padding-top: 10px; padding-bottom: 2px; }}
    QLabel#ErrorLabel {{ color: {ERROR}; font-size: {FE}px; {BGT} {BN} padding: 0; margin: 0; }}
    QLabel#RegexInfoLabel {{ color: {INFO_TEXT}; font-size: {FW}px; {BGT} padding: {PIV}px 0px; }}
    QLabel#QuickApplyInfoLabel {{ color: {TEXT_SUBTLE};}}
    QLabel#QuickApplyKeepInfoLabel {{ color: {TEXT_SUBTLE}; font-size: {FW}px; }}
    QLabel#SearchBarRestartLabel {{ color: {ERROR}; font-size: {FW}px; }}
    QWidget#custom_list_container {{ {BGT} }}
    QLabel#ThemeErrorLabel {{ color: {ERROR}; font-size: {FE}px; {BGT} {BN} padding: 0; margin: 0; }}
    """
    return dynamic_qss

def get_splash_title_style(colors):
    ACCENT = colors.get("accent", "#FF1796")
    FST = THEME_TYPOGRAPHY["font_splash_title"]
    return f"font-size: {FST}px; font-weight: bold; color: {ACCENT};"

def get_splash_main_style(colors, spacing, typo):
    return f"""
        QWidget#SplashContainer {{
            background-color: {colors.get('bg', '#09090b')};
            border-radius: {spacing.get('radius_medium', '10px')};
        }}
        QLabel {{
            color: {colors.get('text_main', '#e4e4e7')};
            font-size: {typo.get('font_splash_status', 16)}px;
            font-weight: bold;
        }}
        QProgressBar {{
            border: none;
            border-radius: {spacing.get('radius_small', '8px')};
            background-color: {colors.get('hover', '#27272a')};
            height: {spacing.get('splash_progress_height', 10)}px;
        }}
        QProgressBar::chunk {{
            background-color: {colors.get('accent', '#FF1796')};
            border-radius: {spacing.get('radius_small', '8px')};
        }}
    """

def get_splash_overlay_style(colors, spacing, typo):
    return f"""
        QWidget {{ background-color: rgba(0, 0, 0, 180); }}
        QWidget#SplashInner {{
            background-color: {colors.get('bg', '#09090b')};
            border-radius: {spacing.get('radius_medium', '10px')};
        }}
        QLabel {{
            color: {colors.get('text_main', '#e4e4e7')};
            font-size: {typo.get('font_splash_label', 18)}px;
            font-weight: bold;
            background-color: transparent;
        }}
    """

def get_bettermotion_overlay_style(colors):
    hover_color = colors.get('hover', '#27272a')
    return f"""
        background-color: rgba(24, 24, 27, 0.9);
        border-radius: 12px;
        border: 1px solid {hover_color};
    """
