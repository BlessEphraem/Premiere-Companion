# Premiere Companion

<p align="center">
  <img src="./Icons/icon.ico" width="200" alt="Logo Premiere Companion">
</p>

**Premiere Companion** is a productivity tool for Adobe Premiere Pro that lets you instantly apply **video effects**, **audio effects**, **transitions**, and **presets** — all from a fast, keyboard-driven search bar without ever leaving your timeline.
> Think of it as a Excalibur plugin alternatives, but can apply Presets too, and for FREE and Open Source.

<p align="center">
  <img src=".docs/medias/preview_SearchBar.gif" width="100%" alt="Preview Search Bar">
</p>

## ✨ Features
- **💫 NEW: Apply anything with Custom Hotkeys** — Create as many shortcuts as you like to apply effects, transitions, and even presets.
- **⚡ Instant Search Bar** — Summon a floating search bar from anywhere with a fully customizable shortcut (default: `Ctrl+Space`) while Premiere Pro is in focus.
- **🗂️ Category Navigation** — Use the `←` / `→` arrow keys to cycle through element categories (Transitions, Video FX, Audio FX, Presets, All) without touching the mouse.
- **🔍 Live Filtering** — Results update as you type with a smart scoring algorithm that prioritizes recently used items.
- **🎯 Preset Support (Quick Apply)** — Apply your saved Premiere Pro presets automatically using recorded mouse positions and hardware-level input simulation. _(Requires initial configuration — see [How to enable Quick Apply](#-how-to-enable-quick-apply-apply-presets)_
- **🔌 WebSocket Bridge** — Communicates with Premiere Pro in real-time through a dedicated UXP plugin.

<p align="center">
  <img src=".docs/medias/preview_ApplyingEffectsAndPresets.gif" width="100%" alt="Applying Effects and Presets">
</p>

## ⚠️ Known Limitation - Undo Grouping: Currently, applying an effect to multiple clips requires pressing Undo (Ctrl/Cmd+Z) for each individual clip to revert the changes. I am actively working on an update to group these into a single Undo action!

## 📋 Prerequisites
Before using Premiere Companion, make sure you have:
- **Adobe Premiere Pro 25.6.1** or a **Beta version** that supports **UXP plugins**.
- The **Premiere Companion UXP Plugin** installed inside Premiere Pro.
> ⚠️ **The UXP plugin is mandatory regardless of which installation method you choose.** Premiere Companion cannot communicate with Premiere Pro without it.
📦 **Plugin download & installation guide:** [Premiere Companion (Listener)](https://github.com/BlessEphraem/Premiere-Companion-UXP)

---

## 🚀 Installation
> ⚠️ **Reminder:** Install the UXP plugin first before proceeding. See [Prerequisites] above.

### ✅ Recommended — Download the Setup / Portable version
1. Choose the "setup.exe" or the "portable.zip" [**here**](https://github.com/BlessEphraem/Premiere-Companion/releases/tag/3.0.0) page.
2. Install.
* For the Portable version:
The release build is pre-packaged and ready to use out of the box.

### 🛠️ From Source — Run the `.pyw` Script
If you prefer to run directly from source, clone this repo.
**Before running `Premiere Companion.pyw`, install the required dependencies:**
```bash
pip install PyQt6 pywin32 pyautogui websockets pynput keyboard
```
> ⚠️ **Make sure to run the script as Administrator.** Some features (global keyboard hooks, mouse simulation, hardware input injection) require elevated privileges.

---

## 🏁 First Run

<p align="center">
  <img src=".docs/medias/preview_MainPage.png" width="50%" alt="Preview Search Bar">
</p>

By default, **transitions, video effects, and audio effects** work immediately once connected. To make Preset apply-able, it will need a further confguration.

### 1. Connect to Premiere Pro
1. Open Premiere Pro and load the **Premiere Companion** plugin (Look at the top bar, `Window > UXP Plugins > Premiere Companion (Listener)`).
2. In both the plugin panel and the Premiere Companion application, verify that the **WebSocket Port** matches exactly. You can check and adjust this in **Settings → Port & Connection Settings**.
3. Enable **Auto-Connect** in both the plugin and the application — this is **strongly recommended** to maintain a stable connection across sessions.
4. When the connection is established:
    - The **console** at the bottom of the app will display a green confirmation message.
    - The **plugin panel** will also indicate that it is connected.

### 2. Fetch Effects & Transitions
1. In Premiere Companion, click **"Fetch Effects"** and wait for the process to complete.
    > ℹ️ The application may appear unresponsive during the sync — this is normal. Do not close it, just wait.
2. Once done, all your effects and transitions are indexed and searchable.

🎉 You can now apply any effect or transition directly via the search bar using **`Ctrl+Space`** while Premiere Pro is focused. This shortcut is configurable in the **Keymaps** page.


### 🧹 Recommended: Apply a Regex Clean (Transition Names)
> This step is **strongly recommended** if you want clean, readable names for your transitions.
The Premiere Pro API does not expose a clean way to retrieve formatted transition names — raw internal names often include plugin prefixes, codes, and technical identifiers (e.g., `AE.ADBE Cross Dissolve PrTr`).
To fix this, go to the **Regex Cleaner** page and use one of these options:
- **🤖 Auto-Generate Rules** — Analyzes all your fetched transitions and automatically builds cleanup rules. Works well for most setups.
- **📄 Import my personal rules file** — Download and use my pre-made regex ruleset, crafted specifically for a clean Premiere Pro effect list. _(Link coming soon)_
Rules are applied in order and can be individually reordered, edited, or deleted.

## ⚡ How to Enable 'Quick Apply' (Apply Presets)
Quick Apply lets you apply your saved Premiere Pro presets directly from the search bar, using screen capture and hardware-level mouse/keyboard simulation.

### How it works
Quick Apply works by recording the **exact screen position** of a preset icon in Premiere Pro's effect browser. When you apply a preset from the search bar, the app automatically:

1. Opens the Effects panel
2. Types the preset name in the search box
3. Drags the preset from its recorded position to your timeline cursor
For this to work reliably, **all your presets must be stored at the same folder depth** in Premiere Pro's preset browser, so that a search always returns exactly one result at a consistent screen position.

### Setup Steps
**Step 1 — Assign Keybinds**
Go to the **Keymaps** page and make sure the following shortcuts match exactly what you have configured in Premiere Pro:

|Action|Default|
|---|---|
|Window > Effect|`Shift+2`|
|Search Find Box|`Shift+F`|
|Window > Timelines|`Shift+3`|
> ⚠️ This is critical. If these shortcuts don't match Premiere Pro's actual keybindings, preset capture and application will fail.

**Step 2 — Run the Configuration Wizard**
1. Go to **Settings** and click **"⚙️ Configure"** under the Quick Apply section.
2. Select your **Premiere Pro version** from the dropdown. This is used exclusively to locate your preset file on disk — it has **no effect** on how effects and transitions are fetched (that happens automatically via the plugin).
3. In Premiere Pro's effect browser, search for **one specific preset** — make sure only **one result** appears in the list.
4. Click **"🎯 Launch Calibration (5s)"** in the wizard, then move your mouse cursor over the preset icon in Premiere Pro within the 5-second countdown.
5. After 5 seconds, the app will verify that the Effects search bar is correctly focused. If validation fails, double-check your keybinds.

**Step 3 — Keep Your Layout Stable**
> ⚠️ Do not move or resize the Premiere Pro window after calibration. The recorded position is absolute. If the window moves, you must re-run the calibration wizard.

**Step 4 — Fetch Presets**
Click **"Fetch Presets"** in the main application. Your presets will be indexed and will appear in the search bar under the `Preset` category.

That's it — you can now apply presets instantly from the search bar! 🎉

---

## 📖 Usage Guide
Once configured, for a detailed breakdown of how to use the search bar (keyboard navigation, category filtering, transition alignment, recent items, and more), see the [**Search Bar Guide →**](.docs/SearchBar.md) ***IN PROGRESS***.
> ⚠️ Only Transition, native Premiere Video/Audio Effect will work. If you wan't to apply Presets, you need some configuration. See the []

---

## 🛠️ Tech Stack
- **Python** with PyQt6 (GUI)
- **WebSocket** bridge between the app and Premiere Pro's UXP plugin
- **Win32 API** for window focus management and hardware-level input injection
- **PyAutoGUI + pynput** for mouse simulation (Quick Apply)
- **XML parsing** for preset extraction from Premiere Pro's `.prfpset` file

## 📄 License

GPL-3.0 license — see [LICENSE](LICENSE) for details.