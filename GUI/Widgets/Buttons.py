# GUI/Widgets/Buttons.py
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import QSize
from Core.functions.icon_loader import icon
from Core.theme_qss import THEME_SPACING


def create_sync_button(click_handler, parent=None):
    """Crée un bouton Sync avec style PrimaryButton (bleu).
    
    Args:
        click_handler: Fonction appelée au clic
        parent: Widget parent (optionnel)
    
    Returns:
        QPushButton configuré
    """
    btn = QPushButton(parent)
    btn.setIcon(icon("sync", size=THEME_SPACING["icon_small"]))
    btn.setText(" Sync")
    btn.setFixedHeight(THEME_SPACING["height_search_bar"])
    btn.setObjectName("PrimaryButton")
    btn.clicked.connect(click_handler)
    return btn
