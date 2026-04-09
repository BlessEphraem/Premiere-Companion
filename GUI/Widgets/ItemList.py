# GUI/Widgets/itemlist.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from Modules.apply_effect import EffectApplier
from Core.theme_qss import THEME_USER_COLORS, THEME_SPACING
from Core.configs.labels_config import get_labels, get_display_label, is_video, is_audio, is_transition, is_preset, is_command

class EffectItemWidget(QWidget):
    def __init__(self, effect_name, match_name, effect_type, parent_gui, parent_widget=None, show_apply=True):
        super().__init__(parent_widget)
        self.parent_gui = parent_gui
        self.match_name = match_name 
        self.effect_type = effect_type

        self.setObjectName("effectItem")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(THEME_SPACING["padding_small"], THEME_SPACING["padding_tiny"], THEME_SPACING["padding_small"], THEME_SPACING["padding_tiny"])

        type_key = "unknown"
        if is_command(effect_type): type_key = "TagCommand"
        elif is_preset(effect_type): type_key = "TagPreset"
        elif is_transition(effect_type): type_key = "TagTransition"
        elif is_video(effect_type): type_key = "TagVideo"
        elif is_audio(effect_type): type_key = "TagAudio"

        self.lbl_tag = QLabel(f" {effect_type} ")
        self.lbl_tag.setObjectName("EffectTag")
        self.lbl_tag.setProperty("type", type_key)
        
        self.lbl_name = QLabel(effect_name)
        self.lbl_name.setObjectName("effectName")
        
        self.btn_apply = None
        if show_apply:
            self.btn_apply = QPushButton("Apply")
            self.btn_apply.setObjectName("applyButton")
            self.btn_apply.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_apply.clicked.connect(self.on_apply_clicked)
            self.btn_apply.setVisible(False)
        
        layout.addWidget(self.lbl_tag)
        layout.addWidget(self.lbl_name)
        layout.addStretch()
        if self.btn_apply:
            layout.addWidget(self.btn_apply)

    def on_apply_clicked(self):
        if is_command(self.effect_type):
            if self.match_name == "CMD.QA":
                from Core.functions.windows import create_window
                window = create_window("quick_apply", self.parent_gui)
                self.parent_gui.register_child_window(window)
                window.show()
            elif self.match_name == "CMD.BM":
                self.parent_gui.append_log(" Better Motion is triggered via its hotkey.", THEME_USER_COLORS["info"])
            return
        if is_transition(self.effect_type):
            self.parent_gui._show_transition_safe(self.match_name, self.effect_type)
            return
        if "PRST" in self.effect_type:
            self.parent_gui.append_log(f" Apply Preset: '{self.match_name}'", THEME_USER_COLORS["info"])
            from Modules.apply_preset import PresetApplier
            config = PresetApplier.load_config()
            is_quick_apply = config.get("quick_apply_enabled", False) if config else False
            keep_on_mouse = config.get("keep_on_mouse", False) if config else False
            result = PresetApplier.apply_preset_to_premiere(self.match_name, is_quick_apply, keep_on_mouse)
            if isinstance(result, tuple):
                success, msg = result
            else:
                success, msg = True, result
            
            if success:
                self.parent_gui.show_tooltip_error("Action successful")
                self.parent_gui.append_log(f" {msg}", THEME_USER_COLORS["success"])
            else:
                self.parent_gui.show_tooltip_error("Action cancelled")
                self.parent_gui.append_log(f" {msg}", THEME_USER_COLORS["error"])
        else:
            self.parent_gui.append_log(f" Apply effect '{self.match_name}'", THEME_USER_COLORS["info"])
            try:
                EffectApplier.apply_effect_to_premiere(self.match_name, self.effect_type)
            except Exception as e:
                self.parent_gui.append_log(f" Error: {e}", THEME_USER_COLORS["error"])

    def enterEvent(self, event):
        if self.btn_apply:
            self.btn_apply.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.btn_apply:
            self.btn_apply.setVisible(False)
        super().leaveEvent(event)
