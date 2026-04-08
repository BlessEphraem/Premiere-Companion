# Core/functions/icon_loader.py
import os
import json
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QSize, QByteArray
from Core.paths import get_app_path, get_data_path
from Core.theme_qss import THEME_USER_COLORS

_theme_cache = None

def _load_theme_colors():
    global _theme_cache
    if _theme_cache is not None:
        return _theme_cache
        
    colors = THEME_USER_COLORS.copy()
    path = get_data_path("theme.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                colors.update(json.load(f))
        except Exception:
            pass
    _theme_cache = colors
    return colors

def reload_theme():
    global _theme_cache
    _theme_cache = None

def _get_icon_colors():
    colors = _load_theme_colors()
    return {
        "color": colors.get("icon_color", "#e4e4e7"),
        "size": 24
    }

def _colorize_svg(svg_content, color_hex):
    """Remplace les couleurs dans le contenu SVG par la couleur choisie."""
    # Handle rgba if passed
    if color_hex.startswith("rgba"):
        return svg_content.replace('currentColor', color_hex).replace('fill="none"', f'fill="{color_hex}"')
        
    return svg_content.replace('currentColor', color_hex).replace('fill="none"', f'fill="{color_hex}"')

def icon(name, color=None, size=None):
    defaults = _get_icon_colors()
    color = color if color is not None else defaults["color"]
    size = size if size is not None else defaults["size"]
    
    icon_path = os.path.join(get_app_path(), "Assets", "icons", f"{name}.svg")
    if os.path.exists(icon_path):
        with open(icon_path, "r", encoding="utf-8") as f:
            svg_content = f.read()

        svg_content = _colorize_svg(svg_content, color)

        renderer = QSvgRenderer(QByteArray(svg_content.encode()))
        if renderer.isValid():
            pixmap = QPixmap(QSize(size, size))
            pixmap.fill(QColor(0, 0, 0, 0))
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            return QIcon(pixmap)
    return QIcon()

def icon_nav(name, color=None, size=None):
    color = color if color is not None else _load_theme_colors()["icon_nav"]
    return icon(name, color=color, size=size)

def icon_pixmap(name, color=None, size=None):
    defaults = _get_icon_colors()
    color = color if color is not None else defaults["color"]
    size = size if size is not None else defaults["size"]
    
    icon_path = os.path.join(get_app_path(), "Assets", "icons", f"{name}.svg")
    if os.path.exists(icon_path):
        with open(icon_path, "r", encoding="utf-8") as f:
            svg_content = f.read()

        svg_content = _colorize_svg(svg_content, color)

        renderer = QSvgRenderer(QByteArray(svg_content.encode()))
        if renderer.isValid():
            pixmap = QPixmap(QSize(size, size))
            pixmap.fill(QColor(0, 0, 0, 0))
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            return pixmap
    return QPixmap()
