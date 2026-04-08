# GUI/Widgets/splash.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QProgressBar, 
                             QApplication, QHBoxLayout, QFrame)
from PyQt6.QtCore import Qt, QRect
from Core.theme_qss import (get_splash_main_style, get_splash_title_style, 
                             get_splash_overlay_style, THEME_SPACING, THEME_TYPOGRAPHY)

class SplashScreen(QWidget):
    """
    Standalone splash screen window used during application boot.
    """
    def __init__(self, colors):
        super().__init__()
        self.colors = colors
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.container = QWidget()
        self.container.setObjectName("SplashContainer")
        self.container.setFixedSize(THEME_SPACING["splash_width"], THEME_SPACING["splash_height"])
        self.container.setStyleSheet(get_splash_main_style(self.colors, THEME_SPACING, THEME_TYPOGRAPHY))
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(THEME_SPACING["padding_splash"], THEME_SPACING["padding_splash"], THEME_SPACING["padding_splash"], THEME_SPACING["padding_splash"])
        container_layout.setSpacing(THEME_SPACING["spacing_element"])

        # Title
        self.title_label = QLabel("Premiere Companion")
        self.title_label.setStyleSheet(get_splash_title_style(self.colors))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.title_label)

        # Status
        self.status_label = QLabel("Loading components...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        container_layout.addWidget(self.progress_bar)

        layout.addWidget(self.container)
        
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.center() - QRect(0, 0, THEME_SPACING["splash_width"], THEME_SPACING["splash_height"]).center())

    def update_progress(self, value, text=None):
        self.progress_bar.setValue(value)
        if text:
            self.status_label.setText(text)
        QApplication.processEvents()


class SplashOverlay(QWidget):
    """
    Full-window overlay shown during blocking operations (fetching effects).
    Includes a title, status message, and a progress bar.
    """
    def __init__(self, parent, colors):
        super().__init__(parent)
        self.colors = colors
        self.init_ui()

    def init_ui(self):
        # 1. Overlay styling
        self.setStyleSheet(get_splash_overlay_style(self.colors, THEME_SPACING, THEME_TYPOGRAPHY))
        if self.parent():
            self.setGeometry(self.parent().rect())
        
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 2. Centered container card
        self.container = QWidget()
        self.container.setObjectName("SplashInner")
        self.container.setFixedSize(THEME_SPACING["splash_inner_width"], THEME_SPACING["splash_inner_height"])
        self.container.setStyleSheet(get_splash_main_style(self.colors, THEME_SPACING, THEME_TYPOGRAPHY))
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(THEME_SPACING["padding_splash_inner"], THEME_SPACING["padding_splash_inner"], THEME_SPACING["padding_splash_inner"], THEME_SPACING["padding_splash_inner"])
        container_layout.setSpacing(THEME_SPACING["spacing_tight"])

        # Title
        self.title_label = QLabel("Syncing...")
        self.title_label.setStyleSheet(get_splash_title_style(self.colors))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.title_label)

        # Status
        self.status_label = QLabel("Please wait...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 0) # Indeterminate by default
        container_layout.addWidget(self.progress_bar)

        main_layout.addWidget(self.container)

    def set_title(self, text):
        self.title_label.setText(text)

    def set_status(self, text):
        self.status_label.setText(text)

    def set_progress(self, current, total):
        if total > 0:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(current)
        else:
            self.progress_bar.setRange(0, 0)

    def update_geometry(self):
        if self.parent():
            self.setGeometry(self.parent().rect())

    def showEvent(self, event):
        self.update_geometry()
        super().showEvent(event)
