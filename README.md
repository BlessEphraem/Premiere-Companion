# 🎬 Premiere Companion
**Premiere Companion** is a productivity tool for Adobe Premiere Pro that lets you instantly apply **video effects**, **audio effects**, **transitions**, and **presets** — all from a fast, keyboard-driven search bar without ever leaving your timeline.
> Think of it as a Excalibur plugin alternatives, but can apply Presets too, and for FREE and Open Source.

## ✨ Features
- **⚡ Instant Search Bar** — Summon a floating search bar from anywhere with a fully customizable shortcut (default: `Ctrl+Space`) while Premiere Pro is in focus.
- **🗂️ Category Navigation** — Use the `←` / `→` arrow keys to cycle through element categories (Transitions, Video FX, Audio FX, Presets, All) without touching the mouse.
- **🔍 Live Filtering** — Results update as you type with a smart scoring algorithm that prioritizes recently used items.
- **🎯 Preset Support (Quick Apply)** — Apply your saved Premiere Pro presets automatically using recorded mouse positions and hardware-level input simulation. _(Requires initial configuration — see [How to enable Quick Apply].)_
- **🔌 WebSocket Bridge** — Communicates with Premiere Pro in real-time through a dedicated UXP plugin.

---

## 📋 Prerequisites
Before using Premiere Companion, make sure you have:
- **Adobe Premiere Pro 25.6.1** or a **Beta version** that supports **UXP plugins**.
- The **Premiere Companion UXP Plugin** installed inside Premiere Pro.
> ⚠️ **The UXP plugin is mandatory regardless of which installation method you choose.** Premiere Companion cannot communicate with Premiere Pro without it.
📦 **Plugin download & installation guide:** [https://your-plugin-link.example.com](https://your-plugin-link.example.com/)

---

## 🚀 How to Install
> ⚠️ **Reminder:** Install the UXP plugin first before proceeding. See [Prerequisites] above.

### ✅ Recommended — Download the Latest Release
1. Go to the [**Releases**](https://claude.ai/releases) page.
2. Download the latest packaged build.
3. Extract and run **Premiere Companion** — no additional setup required.
The release build is pre-packaged and ready to use out of the box.

### 🛠️ From Source — Run the `.pyw` Script
If you prefer to run directly from source:
**Before running `Premiere Companion.pyw`, install the required dependencies:**
```bash
pip install PyQt6 pywin32 pyautogui websockets pynput keyboard
```
> ⚠️ **Make sure to run the script as Administrator.** Some features (global keyboard hooks, mouse simulation, hardware input injection) require elevated privileges.

---

## 🏁 First Run
By default, **transitions, video effects, and audio effects** work immediately once connected. Presets require an additional configuration step described [below].

### 1. Connect to Premiere Pro
1. Open Premiere Pro and load the **Premiere Companion** panel from the UXP plugin manager.
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

---

## 📖 Usage Guide
Once configured, for a detailed breakdown of how to use the search bar (keyboard navigation, category filtering, transition alignment, recent items, and more), see the [**Search Bar Guide →**](.wiki/Searchbar.md).
> ⚠️ Only Transition, native Premiere Video/Audio Effect will work. If you wan't to apply Presets, you need some configuration. See the []

---



---

## 🛠️ Tech Stack
- **Python** with PyQt6 (GUI)
- **WebSocket** bridge between the app and Premiere Pro's UXP plugin
- **Win32 API** for window focus management and hardware-level input injection
- **PyAutoGUI + pynput** for mouse simulation (Quick Apply)
- **XML parsing** for preset extraction from Premiere Pro's `.prfpset` file

## 📄 License

MIT License — see [LICENSE]() for details.