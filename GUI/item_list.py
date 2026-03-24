# GUI/item_list.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from Modules.apply_preset import PresetApplier
from Modules.apply_effect import EffectApplier 

class EffectItemWidget(QWidget):
    def __init__(self, effect_name, match_name, effect_type, parent_gui, parent_widget=None):
        super().__init__(parent_widget)
        self.parent_gui = parent_gui
        self.match_name = match_name 
        self.effect_type = effect_type

        self.setObjectName("effectItem")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        # Mapping for QSS
        type_key = "unknown"
        if "FxVideo" in effect_type and "Transition" not in effect_type: type_key = "TagVideo"
        elif "FxAudio" in effect_type and "Transition" not in effect_type: type_key = "TagAudio"
        elif "Transition" in effect_type: type_key = "TagTransition"
        elif "Preset" in effect_type: type_key = "TagPreset"

        # Tag Label
        self.lbl_tag = QLabel(f"[{effect_type}]")
        self.lbl_tag.setObjectName("EffectTag")
        self.lbl_tag.setProperty("type", type_key)
        self.lbl_tag.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self.lbl_tag)

        # Naming Label
        self.lbl_name = QLabel(effect_name)
        self.lbl_name.setObjectName("EffectNameLabel")
        self.lbl_name.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self.lbl_name, stretch=1)

        self.btn_apply = QPushButton("Apply")
        self.btn_apply.setObjectName("ApplyButton")
        self.btn_apply.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_apply.setVisible(False) 
        self.btn_apply.clicked.connect(self.on_apply_clicked)
        layout.addWidget(self.btn_apply)

    def on_apply_clicked(self):
        if "Transition" in self.effect_type:
            self.parent_gui.search_bar_overlay.show_transition_options(self.match_name, self.effect_type)
            return

        if self.effect_type == "Preset":
            self.parent_gui.append_log(f"⚡ Attempting to apply Preset: '{self.match_name}'", "#55ccff")
            is_quick_apply = self.parent_gui.settings.get("quick_apply_enabled", False)
            
            result = PresetApplier.apply_preset_to_premiere(self.match_name, is_quick_apply)
            if isinstance(result, tuple):
                success, msg = result
            else:
                success, msg = True, result
            
            if success:
                self.parent_gui.show_tooltip_error("Action successful")
                self.parent_gui.append_log(f"✅ {msg}", "#55ff55")
            else:
                self.parent_gui.show_tooltip_error("Action cancelled")
                self.parent_gui.append_log(f"❌ {msg}", "#ff5555")
        else:
            self.parent_gui.append_log(f"⚡ Apply effect '{self.match_name}'", "#55ccff")
            try:
                EffectApplier.apply_effect_to_premiere(self.match_name, self.effect_type)
            except Exception as e:
                self.parent_gui.append_log(f"❌ Error: {e}", "#ff5555")