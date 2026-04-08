"""
Utils/scaffold_page.py
----------------------
Interactive CLI generator for new Pages, Widgets, and Features.
Follows all Premiere Companion conventions (imports, theming, signal/slot,
window registration in Core/functions/windows.py).

Usage:
    python Utils/scaffold_page.py
"""

import os
import sys
import re

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WINDOWS_PY   = os.path.join(ROOT, "Core", "functions", "windows.py")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ask(prompt, choices=None, default=None):
    while True:
        suffix = ""
        if choices:
            suffix = f" [{'/'.join(choices)}]"
        if default is not None:
            suffix += f" (default: {default})"
        raw = input(f"  {prompt}{suffix}: ").strip()
        if not raw and default is not None:
            return str(default)
        if choices and raw.lower() not in [c.lower() for c in choices]:
            print(f"    Please enter one of: {', '.join(choices)}")
            continue
        return raw

def ask_bool(prompt, default=False):
    answer = ask(prompt, choices=["y", "n"], default="y" if default else "n")
    return answer.lower() == "y"

def ask_int(prompt, default=None):
    while True:
        raw = ask(prompt, default=str(default) if default is not None else None)
        try:
            return int(raw)
        except ValueError:
            print("    Please enter a number.")

def to_pascal(name):
    return "".join(w.capitalize() for w in name.replace("-", " ").replace("_", " ").split())

def to_snake(name):
    return name.strip().lower().replace(" ", "_").replace("-", "_")

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        if not ask_bool(f"File exists: {os.path.relpath(path, ROOT)}  Overwrite?", default=False):
            print(f"    Skipped.")
            return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"    Created: {os.path.relpath(path, ROOT)}")
    return True

def separator(title=""):
    width = 62
    if title:
        pad = (width - len(title) - 2) // 2
        print(f"\n{'─' * pad} {title} {'─' * (width - pad - len(title) - 2)}")
    else:
        print(f"\n{'─' * width}")

# ---------------------------------------------------------------------------
# windows.py patcher
# ---------------------------------------------------------------------------

def patch_windows_py(snake_name, class_name, placement, win_w, win_h):
    """
    Inserts the WINDOW_SIZES entry and create_window() branch into windows.py.
    Returns True on success, False if patching failed (file then unchanged).
    """
    with open(WINDOWS_PY, "r", encoding="utf-8") as f:
        src = f.read()

    # --- 1. WINDOW_SIZES entry ---
    w_val = f'"{win_w}"' if isinstance(win_w, str) else str(win_w)
    h_val = f'"{win_h}"' if isinstance(win_h, str) else str(win_h)
    size_line = f'    "{snake_name}": {{"width": {w_val}, "height": {h_val}}},\n'

    # Insert just before the closing } of the WINDOW_SIZES dict
    sizes_close = re.search(r'(\n}\s*\n\n)', src)
    if not sizes_close:
        print("    Could not locate end of WINDOW_SIZES dict. Patch skipped.")
        return False
    src = src[:sizes_close.start()] + "\n" + size_line + src[sizes_close.start():]

    # --- 2. Import for the new page at the top of the file ---
    import_line = f"from GUI.Pages.{snake_name} import {class_name}\n"
    # Insert after the last existing "from GUI.Pages..." import
    last_import = list(re.finditer(r"^from GUI\.Pages\.\S+ import \S+\n", src, re.MULTILINE))
    if last_import:
        ins = last_import[-1].end()
        src = src[:ins] + import_line + src[ins:]
    else:
        # Fallback: insert after the last import block
        last_any = list(re.finditer(r"^(?:import|from) .+\n", src, re.MULTILINE))
        if last_any:
            ins = last_any[-1].end()
            src = src[:ins] + import_line + src[ins:]

    # --- 3. create_window() branch ---
    # Insert before the final `else: raise ValueError` clause
    else_match = re.search(r"(\n    else:\n        raise ValueError)", src)
    if not else_match:
        print("    Could not locate else clause in create_window(). Patch skipped.")
        return False

    if placement == "child":
        branch = (
            f"\n    elif window_type == \"{snake_name}\":\n"
            f"        window = {class_name}(parent)\n"
            f"        window.setParent(parent)\n"
            f"        apply_window_config(window, \"{snake_name}\", \"{class_name.replace('Page', '')}\")\n"
            f"        return window\n"
        )
    else:  # dialog
        branch = (
            f"\n    elif window_type == \"{snake_name}\":\n"
            f"        from PyQt6.QtWidgets import QVBoxLayout\n"
            f"        dialog = QDialog(parent)\n"
            f"        dialog.setWindowTitle(\"{class_name.replace('Page', '')}\")\n"
            f"        apply_window_config(dialog, \"{snake_name}\")\n"
            f"        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)\n"
            f"        layout = QVBoxLayout(dialog)\n"
            f"        page = {class_name}(parent)\n"
            f"        layout.addWidget(page)\n"
            f"        return dialog\n"
        )

    src = src[:else_match.start()] + branch + src[else_match.start():]

    with open(WINDOWS_PY, "w", encoding="utf-8") as f:
        f.write(src)

    print(f"    Patched: Core/functions/windows.py")
    return True

# ---------------------------------------------------------------------------
# Template builders
# ---------------------------------------------------------------------------

def build_page(class_name, snake_name, opts):
    imports = [
        "from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton",
        "from Core.theme_qss import THEME_SPACING, THEME_USER_COLORS",
        "from Core.functions.icon_loader import icon",
    ]
    if opts["has_list"]:
        imports += [
            "from PyQt6.QtWidgets import QListWidget, QListWidgetItem",
            "from PyQt6.QtCore import QSize",
        ]
    if opts["has_config"]:
        imports += [
            f"from Core.configs.{snake_name}_config import DEFAULT_{snake_name.upper()}_CONFIG",
            "from Core.paths import get_data_path",
            "import json, os",
        ]
    if opts["needs_premiere"]:
        imports.append("from Core.functions.server import send_to_plugin")

    list_block = (
        "\n"
        "        self.list_widget = QListWidget()\n"
        "        self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)\n"
        "        layout.addWidget(self.list_widget)\n"
    ) if opts["has_list"] else ""

    action_block = (
        "\n"
        "        btn_layout = QHBoxLayout()\n"
        "        btn_action = QPushButton()\n"
        "        btn_action.setIcon(icon(\"check\"))\n"
        "        btn_action.setText(\" Apply\")\n"
        "        btn_action.setObjectName(\"AccentButton\")\n"
        "        btn_action.clicked.connect(self.on_action)\n"
        "        btn_layout.addStretch()\n"
        "        btn_layout.addWidget(btn_action)\n"
        "        layout.addLayout(btn_layout)\n"
    ) if opts["has_action_btn"] else ""

    premiere_method = (
        "\n"
        "    def send_to_premiere(self, payload: dict):\n"
        "        \"\"\"Send a WebSocket command to the Premiere Pro plugin.\"\"\"\n"
        "        success = send_to_plugin(payload)\n"
        "        if not success:\n"
        "            self.mw.append_log(\" Premiere is not connected.\", THEME_USER_COLORS[\"warning\"])\n"
        "        return success\n"
    ) if opts["needs_premiere"] else ""

    config_methods = (
        f"\n"
        f"    def load_config(self) -> dict:\n"
        f"        path = get_data_path(\"{snake_name}_config.json\")\n"
        f"        if os.path.exists(path):\n"
        f"            try:\n"
        f"                with open(path, \"r\", encoding=\"utf-8\") as f:\n"
        f"                    return json.load(f)\n"
        f"            except Exception:\n"
        f"                pass\n"
        f"        return dict(DEFAULT_{snake_name.upper()}_CONFIG)\n"
        f"\n"
        f"    def save_config(self, data: dict):\n"
        f"        path = get_data_path(\"{snake_name}_config.json\")\n"
        f"        os.makedirs(os.path.dirname(path), exist_ok=True)\n"
        f"        with open(path, \"w\", encoding=\"utf-8\") as f:\n"
        f"            json.dump(data, f, indent=4)\n"
    ) if opts["has_config"] else ""

    action_method = (
        "\n"
        "    def on_action(self):\n"
        "        # TODO: implement action logic\n"
        f"        self.mw.append_log(\" {class_name}: action triggered.\", THEME_USER_COLORS[\"info\"])\n"
    ) if opts["has_action_btn"] else ""

    load_method = (
        "\n"
        "    def load_list(self):\n"
        "        \"\"\"Populate the list widget. Replace with your data source.\"\"\"\n"
        "        self.list_widget.clear()\n"
        "        # Example: for item in self.data: self.list_widget.addItem(item)\n"
    ) if opts["has_list"] else ""

    display_title = class_name.replace("Page", "").replace("_", " ")

    return (
        f"# GUI/Pages/{snake_name}.py\n"
        + "\n".join(imports) + "\n"
        "\n\n"
        f"class {class_name}(QWidget):\n"
        f"    def __init__(self, main_window):\n"
        f"        super().__init__()\n"
        f"        self.mw = main_window\n"
        f"        self.init_ui()\n"
        "\n"
        "    def init_ui(self):\n"
        "        layout = QVBoxLayout(self)\n"
        "        layout.setContentsMargins(\n"
        "            THEME_SPACING[\"spacing_page\"], THEME_SPACING[\"spacing_page\"],\n"
        "            THEME_SPACING[\"spacing_page\"], THEME_SPACING[\"spacing_page\"]\n"
        "        )\n"
        "        layout.setSpacing(THEME_SPACING[\"spacing_element\"])\n"
        "\n"
        f"        lbl_title = QLabel(\"{display_title}\")\n"
        "        lbl_title.setObjectName(\"CardLabelBold\")\n"
        "        layout.addWidget(lbl_title)\n"
        + list_block
        + action_block
        + "        layout.addStretch()\n"
        + premiere_method
        + config_methods
        + action_method
        + load_method
    )


def build_widget(class_name, snake_name, opts):
    imports = [
        "from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton",
        "from PyQt6.QtCore import Qt, pyqtSignal",
        "from Core.theme_qss import THEME_SPACING, THEME_USER_COLORS",
        "from Core.functions.icon_loader import icon",
    ]
    if opts["needs_premiere"]:
        imports.append("from Core.functions.server import send_to_plugin")

    return (
        f"# GUI/Widgets/{snake_name}.py\n"
        + "\n".join(imports) + "\n"
        "\n\n"
        f"class {class_name}(QWidget):\n"
        "    # Emit when the widget produces a result the parent should handle\n"
        "    result_signal = pyqtSignal(object)\n"
        "\n"
        "    def __init__(self, parent=None):\n"
        "        super().__init__(parent)\n"
        "        self.init_ui()\n"
        "\n"
        "    def init_ui(self):\n"
        "        layout = QVBoxLayout(self)\n"
        "        layout.setContentsMargins(\n"
        "            THEME_SPACING[\"padding_small\"], THEME_SPACING[\"padding_small\"],\n"
        "            THEME_SPACING[\"padding_small\"], THEME_SPACING[\"padding_small\"]\n"
        "        )\n"
        "        layout.setSpacing(THEME_SPACING[\"spacing_element\"])\n"
        "\n"
        "        # TODO: build widget UI here\n"
        f"        lbl = QLabel(\"{class_name}\")\n"
        "        lbl.setObjectName(\"CardLabelSubtle\")\n"
        "        layout.addWidget(lbl)\n"
    )


def build_config(snake_name):
    upper = snake_name.upper()
    return (
        f"# Core/configs/{snake_name}_config.py\n"
        "\n"
        f"DEFAULT_{upper}_CONFIG = {{\n"
        "    # TODO: add your default configuration keys here\n"
        "    # \"enabled\": False,\n"
        "    # \"value\": 0,\n"
        "}}\n"
    )


def build_logic(class_name, snake_name, opts):
    lines = [f"# Core/functions/{snake_name}.py", f"# Business logic for {class_name}", ""]
    if opts["needs_premiere"]:
        lines.append("from Core.functions.server import send_to_plugin")
    if opts["has_config"]:
        lines += ["from Core.paths import get_data_path", "import json, os"]
    lines.append("")
    if opts["needs_premiere"]:
        lines += [
            "",
            f"def send_{snake_name}_command(payload: dict) -> bool:",
            f"    \"\"\"Send a command to the Premiere Pro plugin for {class_name}.\"\"\"",
            "    return send_to_plugin(payload)",
            "",
        ]
    lines += ["", "# TODO: add your logic here", ""]
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Registration hints
# ---------------------------------------------------------------------------

def print_hints(feature_type, class_name, snake_name, opts, placement):
    separator("Next Steps")
    print()

    if feature_type == "page":
        if placement == "stacked":
            print(f"  1. Open  GUI/Pages/effects_page.py")
            print(f"  2. Add import:")
            print(f"       from GUI.Pages.{snake_name} import {class_name}")
            print(f"  3. Instantiate in EffectsPage.__init__():")
            print(f"       self.{snake_name} = {class_name}(self)")
            print(f"  4. Add to stacked widget:")
            print(f"       self.stacked_widget.addWidget(self.{snake_name})")
            print(f"  5. Add a nav button in  GUI/Widgets/Menu.py")

        elif placement in ("child", "dialog"):
            if opts.get("windows_patched"):
                print(f"  windows.py was patched automatically.")
                print(f"  To open the window from a button:")
                print(f"       from Core.functions.windows import create_window")
                print(f"       win = create_window(\"{snake_name}\", parent=self)")
                print(f"       self.child_windows.append(win)")
                print(f"       win.show()")
            else:
                print(f"  windows.py was NOT patched. Add manually:")
                print(f"  In WINDOW_SIZES:")
                print(f'       "{snake_name}": {{"width": ..., "height": ...}},')
                print(f"  In create_window():")
                if placement == "child":
                    print(f"       elif window_type == \"{snake_name}\":")
                    print(f"           window = {class_name}(parent)")
                    print(f"           window.setParent(parent)")
                    print(f"           apply_window_config(window, \"{snake_name}\", \"...\")")
                    print(f"           return window")
                else:
                    print(f"       elif window_type == \"{snake_name}\":")
                    print(f"           dialog = QDialog(parent)")
                    print(f"           ... (see other dialog examples)")

    elif feature_type == "widget":
        print(f"  Import where needed:")
        print(f"       from GUI.Widgets.{snake_name} import {class_name}")
        print(f"  Instantiate and add to a layout:")
        print(f"       self.{snake_name} = {class_name}(parent=self)")
        print(f"       some_layout.addWidget(self.{snake_name})")

    elif feature_type == "module":
        print(f"  Import your logic where needed:")
        print(f"       from Core.functions.{snake_name} import ...")
        if opts.get("has_config"):
            print(f"  Register config in  Premiere Companion.pyw > ensure_config_defaults()")

    if opts.get("has_config"):
        print()
        print(f"  Config auto-created at  Data/{snake_name}_config.json  on first load.")

    if opts.get("needs_premiere"):
        print()
        print(f"  send_to_plugin() returns False when Premiere is not connected.")
        print(f"  Always handle that case with a log or user feedback.")

    separator()
    print()

# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------

def run():
    separator("Premiere Companion — Feature Scaffold")
    print()
    print("  Generates skeleton files following all project conventions.")
    print("  (theming, signals, config, window registration)")
    print()

    # Step 1 — Type
    separator("Step 1 — Type")
    print()
    print("  page   → GUI/Pages/<name>.py        (a page shown in the UI)")
    print("  widget → GUI/Widgets/<name>.py       (a reusable UI component)")
    print("  module → Core/functions/<name>.py    (background logic)")
    print()
    feature_type = ask("Feature type", choices=["page", "widget", "module"])

    # Step 2 — Name
    separator("Step 2 — Name")
    print()
    raw_name = ask("Feature name (e.g. 'export helper'  or  'ExportHelper')")
    class_name = to_pascal(raw_name)
    snake_name = to_snake(raw_name)

    if feature_type == "page" and not class_name.endswith("Page"):
        class_name += "Page"
    elif feature_type == "widget" and not class_name.endswith(("Widget", "Overlay", "Bar")):
        class_name += "Widget"

    print(f"\n    Class : {class_name}")
    print(f"    File  : {snake_name}.py")
    if not ask_bool("Looks good?", default=True):
        print("  Aborted.")
        return

    # Step 3 — Placement (pages only)
    placement = "stacked"
    win_w, win_h = "auto", "auto"

    if feature_type == "page":
        separator("Step 3 — Window placement")
        print()
        print("  stacked → part of the main window navigation (like Settings, Keymaps)")
        print("  child   → separate sub-window, QWidget-based  (like ThemePage, SearchBarPage)")
        print("  dialog  → modal QDialog                       (like RegexPage, PremiereKeybindsPage)")
        print()
        placement = ask("Placement", choices=["stacked", "child", "dialog"], default="stacked")

        if placement in ("child", "dialog"):
            print()
            use_fixed = ask_bool("Use a fixed window size? (no = auto-sized)", default=False)
            if use_fixed:
                win_w = ask_int("Width (px)", default=540)
                win_h = ask_int("Height (px)", default=400)

    # Step 4 — Capabilities
    separator("Step 4 — Capabilities" if feature_type == "page" else "Step 3 — Capabilities")
    print()

    opts = {}
    opts["needs_premiere"] = ask_bool("Needs to send commands to Premiere Pro (WebSocket)?", default=False)
    opts["has_config"]     = ask_bool("Needs a persistent config file (JSON in Data/)?",     default=False)

    if feature_type in ("page", "widget"):
        opts["has_list"]       = ask_bool("Has a scrollable list (QListWidget)?",            default=False)
        opts["has_action_btn"] = ask_bool("Has an action button (Apply, Save…)?",            default=True)
    else:
        opts["has_list"] = opts["has_action_btn"] = False

    if feature_type == "module":
        opts["create_page"]  = ask_bool("Also generate a GUI/Pages/ skeleton?",              default=False)
        opts["create_logic"] = True
    else:
        opts["create_page"] = opts["create_logic"] = False

    # Generate
    separator("Generating")
    print()

    created = []
    opts["windows_patched"] = False

    if feature_type == "page":
        path = os.path.join(ROOT, "GUI", "Pages", f"{snake_name}.py")
        if write_file(path, build_page(class_name, snake_name, opts)):
            created.append(path)

        if placement in ("child", "dialog"):
            if ask_bool("Auto-patch Core/functions/windows.py?", default=True):
                if patch_windows_py(snake_name, class_name, placement, win_w, win_h):
                    opts["windows_patched"] = True

    elif feature_type == "widget":
        path = os.path.join(ROOT, "GUI", "Widgets", f"{snake_name}.py")
        if write_file(path, build_widget(class_name, snake_name, opts)):
            created.append(path)

    elif feature_type == "module":
        path = os.path.join(ROOT, "Core", "functions", f"{snake_name}.py")
        if write_file(path, build_logic(class_name, snake_name, opts)):
            created.append(path)
        if opts["create_page"]:
            pc = class_name if class_name.endswith("Page") else class_name + "Page"
            pp = os.path.join(ROOT, "GUI", "Pages", f"{snake_name}.py")
            if write_file(pp, build_page(pc, snake_name, opts)):
                created.append(pp)

    if opts["has_config"]:
        cfg = os.path.join(ROOT, "Core", "configs", f"{snake_name}_config.py")
        if write_file(cfg, build_config(snake_name)):
            created.append(cfg)

    if created or opts["windows_patched"]:
        print_hints(feature_type, class_name, snake_name, opts, placement)
        n = len(created) + (1 if opts["windows_patched"] else 0)
        print(f"  Done. {n} file(s) created/patched.")
    else:
        print("\n  Nothing was created.")


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n\n  Cancelled.")
        sys.exit(0)
