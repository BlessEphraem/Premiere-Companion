# GUI/Widgets/Menu.py
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QLineEdit, QLabel
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QEvent, QTimer, QSize, QRect
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen
from Core.functions.icon_loader import icon_nav
from Core.theme_qss import THEME_SPACING, THEME_USER_COLORS
from Core.configs.search_config import SEARCH_TIMER_DELAY
from Core.functions.search import FILTER_MODES


def get_app_icon(size=None, active=False):
    size = size if size is not None else THEME_SPACING["icon_small"]
    from Core.paths import get_app_path, get_data_path
    import os
    import json
    from PyQt6.QtSvg import QSvgRenderer
    from PyQt6.QtGui import QColor, QPixmap, QPainter, QIcon
    
    icon_path = os.path.join(get_app_path(), "Assets", "icons", "icon.svg")
    if os.path.exists(icon_path):
        with open(icon_path, "r", encoding="utf-8") as f:
            svg_data = f.read()
            
        colors = THEME_USER_COLORS.copy()
        theme_path = get_data_path("theme.json")
        if os.path.exists(theme_path):
            try:
                with open(theme_path, "r", encoding="utf-8") as f:
                    colors.update(json.load(f))
            except Exception:
                pass
                
        if active:
            accent_color = colors.get("accent", "#ff1796")
            bg_color = colors.get("bg", "#09090b")
        else:
            accent_color = colors.get("btn_bg", "#18181b")
            bg_color = colors.get("bg", "#09090b")
        
        svg_data = svg_data.replace("#09090b", bg_color)
        svg_data = svg_data.replace("#ff1796", accent_color)
        
        renderer = QSvgRenderer(svg_data.encode('utf-8'))
        
        if renderer.isValid():
            pixmap = QPixmap(QSize(size, size))
            pixmap.fill(QColor(0, 0, 0, 0))
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            return QIcon(pixmap)
    return QIcon()

class AppIconButton(QPushButton):
    sync_triggered = pyqtSignal()

    def __init__(self, size=None):
        super().__init__()
        self.icon_size = size if size is not None else THEME_SPACING["icon_small"]
        self.setIconSize(QSize(self.icon_size, self.icon_size))
        self.setFixedSize(QSize(self.icon_size, self.icon_size))
        self.setObjectName("AppIconBtn")
        self.setFlat(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Hold-to-Sync logic
        self.progress = 0.0
        self.is_pressing = False
        self.hold_timer = QTimer(self) # Parent the timer to self
        self.hold_timer.setInterval(20)
        self.hold_timer.timeout.connect(self._update_progress)
        
        self.set_active(True)

    def _update_progress(self):
        # 2 seconds = 2000ms / 20ms = 100 ticks
        # We add 1.0 per tick to reach 100.0 in 2s
        if self.is_pressing:
            self.progress = min(100.0, self.progress + 1.0)
            if self.progress >= 100.0:
                self.is_pressing = False
                self.hold_timer.stop()
                self.progress = 0.0
                self.sync_triggered.emit()
        else:
            self.progress = max(0.0, self.progress - 1.0)
            if self.progress <= 0.0:
                self.hold_timer.stop()
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_pressing = True
            if not self.hold_timer.isActive():
                self.hold_timer.start()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_pressing = False
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        # 1. Let the button draw its default state (icon, etc.)
        super().paintEvent(event)
        
        # 2. Draw the progress overlay if needed
        if self.progress > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Use icon_nav color from theme (semi-transparent white)
            color_str = THEME_USER_COLORS["icon_nav"]
            pen = QPen(QColor(color_str))
            pen.setWidth(3)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            
            # Area to draw
            margin = 3
            size = self.width() - (margin * 2)
            rect = QRect(margin, margin, size, size)
            
            # Qt angles are in 1/16th of a degree.
            # 0 is 3 o'clock, 90 is 12 o'clock.
            start_angle = 90 * 16
            span_angle = int(-self.progress * 3.6 * 16)
            
            painter.drawArc(rect, start_angle, span_angle)

    def set_active(self, active: bool):
        self.setIcon(get_app_icon(self.icon_size, active))
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)

def _load_app_icon_label(size=None):
    return AppIconButton(size)


class MenuSearchBar(QObject):
    text_changed = pyqtSignal(str)
    filter_changed = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.filter_modes = FILTER_MODES
        self.current_filter_idx = 0
        
        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("MainSearchBar")
        self.search_bar.setFixedHeight(THEME_SPACING["height_search_bar"])
        self.search_bar.setPlaceholderText(THEME_USER_COLORS["app_title"])
        self.search_bar.installEventFilter(self)
        
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._on_timer_expired)
        self.search_bar.textChanged.connect(lambda: self.search_timer.start(SEARCH_TIMER_DELAY))
        
        self._apply_filter_style()
    
    def eventFilter(self, obj, event):
        if obj == self.search_bar and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Right:
                if self.search_bar.cursorPosition() == len(self.search_bar.text()):
                    self.cycle_filter(1)
                    return True
            elif event.key() == Qt.Key.Key_Left:
                if self.search_bar.cursorPosition() == 0:
                    self.cycle_filter(-1)
                    return True
        return super().eventFilter(obj, event)
    
    def cycle_filter(self, direction):
        self.current_filter_idx = (self.current_filter_idx + direction) % len(self.filter_modes)
        self._apply_filter_style()
        self.text_changed.emit(self.search_bar.text())
        self.filter_changed.emit(self.current_filter_idx)
    
    def _apply_filter_style(self):
        mode = self.filter_modes[self.current_filter_idx]
        if mode["name"] == "All":
            placeholder = THEME_USER_COLORS["app_title"]
        else:
            placeholder = f"  Search ({mode['name']})..."
        self.search_bar.setPlaceholderText(placeholder)
        self.search_bar.setProperty("filterType", mode["type"])
        self.search_bar.style().unpolish(self.search_bar)
        self.search_bar.style().polish(self.search_bar)
    
    def _on_timer_expired(self):
        self.text_changed.emit(self.search_bar.text())


class NavIconButton(QPushButton):
    def __init__(self, icon_name, size=None):
        super().__init__()
        self.icon_name = icon_name
        self.icon_size = size if size is not None else THEME_SPACING["icon_small"]
        self.setObjectName("NavButton")
        self.setFixedSize(THEME_SPACING["height_search_bar"], THEME_SPACING["height_search_bar"])
        self.set_active(False)

    def set_active(self, active: bool):
        from Core.theme_qss import THEME_USER_COLORS
        from Core.paths import get_data_path
        import json
        import os
        
        colors = THEME_USER_COLORS.copy()
        theme_path = get_data_path("theme.json")
        if os.path.exists(theme_path):
            try:
                with open(theme_path, "r", encoding="utf-8") as f:
                    colors.update(json.load(f))
            except Exception:
                pass

        if active:
            color = THEME_USER_COLORS["text_white"]
        else:
            color = THEME_USER_COLORS["text_subtle"]

        self.setIcon(icon_nav(self.icon_name, color=color, size=self.icon_size))
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)

class NavMenu:
    @staticmethod
    def create_menu(switch_page_callback, on_search_change=None, on_filter_change=None):
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(THEME_SPACING["spacing_element"])
        
        app_icon = _load_app_icon_label()
        
        menu_search = MenuSearchBar()
        menu_search.text_changed.connect(lambda text: on_search_change(text) if on_search_change else None)
        menu_search.filter_changed.connect(lambda idx: on_filter_change(idx) if on_filter_change else None)
        
        btn_keys = NavIconButton("keyboard")
        btn_settings = NavIconButton("cog")
        
        nav_layout.addWidget(app_icon)
        nav_layout.addWidget(menu_search.search_bar, 1)
        nav_layout.addWidget(btn_keys)
        nav_layout.addWidget(btn_settings)
        
        def navigate_to_effects():
            switch_page_callback(0, app_icon)
        
        menu_search.text_changed.connect(navigate_to_effects)
        app_icon.clicked.connect(lambda: switch_page_callback(0, app_icon))
        btn_keys.clicked.connect(lambda: switch_page_callback(1, btn_keys))
        btn_settings.clicked.connect(lambda: switch_page_callback(2, btn_settings))
        
        result_dict = {
            "btn_home": app_icon,
            "btn_keys": btn_keys,
            "btn_settings": btn_settings,
            "menu_search": menu_search,
        }
        
        return nav_layout, result_dict, [app_icon, btn_keys, btn_settings]
