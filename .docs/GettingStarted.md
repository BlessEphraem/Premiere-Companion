# 📖 Guide
[![](https://img.shields.io/badge/←_Readme-30363d?style=for-the-badge)](../README.md)


# 📋 Prerequisites
Before using Premiere Companion and the plugin, make sure you have:
- **Adobe Premiere Pro 25.6.1** or a **Beta version** that supports **UXP plugins**.

# 🚀 Installation

### ✅ Recommended - Setup / Portable version

Choose the "setup.exe" or the "portable.zip" from the [**Releases page**](https://github.com/BlessEphraem/Premiere-Companion/releases).

<details><summary>
  <strong>🛠️ From Source - Run the `.pyw` Script</strong>
</summary>

If you prefer to run directly from source, clone this repository. Run your terminal as Administrator (required for global hotkeys and mouse simulation) and install the dependencies:
```bash
pip install PyQt6 pywin32 pyautogui websockets pynput
```
> **Optional:** `pip install win11toast` for native Windows 11 toast notifications (falls back to PowerShell automatically if not installed).

</details>

<br/>

# 📡 Connect to Premiere Pro
**Premiere Pro must be closed if you install/update the plugin.**
1. Go to **Settings -> Configure -> Install Plugin**.
2. Open Premiere Pro and load the **Premiere Companion** plugin (Look at the top bar, `Window > UXP Plugins > Premiere Companion (Listener)`).
2. In both the plugin panel and the Premiere Companion application, verify that the **WebSocket Port** matches exactly. You can check and adjust this in **Settings → Premiere Pro → Configure**.

    When the connection is established:
    - The **console** at the bottom of the app will display a green confirmation  essage.
    - The **plugin panel** will also indicate that it is connected.

### 🧹 Recommended - Apply a Regex Clean (Transition Names)
> This step is **strongly recommended** if you want clean, readable names for your transitions.
The Premiere Pro API does not expose a clean way to retrieve formatted transition names - raw internal names often include plugin prefixes, codes, and technical identifiers (e.g., `AE.ADBE Cross Dissolve PrTr`).
To fix this, go to the **Regex** page and use one of these options:
- **🤖 Auto-Generate Rules** - Analyzes all your fetched transitions and automatically builds cleanup rules. Works well for most setups.
- **📄 Import my personal rules file** - Download and use my pre-made regex ruleset, crafted specifically for a clean Premiere Pro effect list. _(Link coming soon)_
Rules are applied in order and can be individually reordered, edited, or deleted.


🎉 You can now apply any effect or transition directly via the search bar using **`Ctrl+Space`** while Premiere Pro is focused. This shortcut is configurable in the **Keymaps** page.

**By default, transitions, video effects, and audio effects work immediately once connected. To make Presets applicable, further configuration is required. (See below.)**

### **[How to Apply Presets ?](QuickApply.md)**

Once done, check every guides on the main Readme page.

[![](https://img.shields.io/badge/←_Readme-30363d?style=for-the-badge)](../README.md#-📖-Guides)