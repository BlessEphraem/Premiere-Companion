# Premiere Companion - Development Notes

<summary><b>📖 Table of Contents</b></summary>

  * [🛠️ Premiere Companion](https://github.com/BlessEphraem/Premiere-Companion)
  * [🛠️ Premiere Companion (Listener)](https://github.com/BlessEphraem/Premiere-Companion-UXP)
  * [🏗️ Roadmap](ROADMAP.md)

</br>

Welcome to the development guide for **Premiere Companion**. This document serves as the architectural reference and onboarding guide for the program. As we continue to scale and maintain this project, these notes will help us keep the codebase clean, modular, and easy to understand.

## 🛠️ Tech Stack & Technologies

To effectively maintain and expand this application, you should be familiar with the following stack:

- **Language:** Python 3
- **GUI Framework:** PyQt6 (using dynamic QSS for styling)
- **Network & Concurrency:** `asyncio` and `websockets` (used to maintain a real-time duplex connection with Adobe Premiere Pro).
- **OS-Level Integration (Windows):** 
  - `ctypes` and `win32gui` for global hotkey registration, process locking, and window focus management.
  - `pyautogui` for input simulation (e.g., forcing modifier key releases during macro execution).
- **Data Persistence:** Local JSON files (for configurations, keybinds, and themes).

> **Architectural Note:** This application is heavily optimized for the Windows OS due to its deep reliance on `ctypes` and Win32 APIs for global hotkeys and window management. Cross-platform support would require significant abstraction of the `Core/hotkeys.py` and input simulation modules.

---

## 🏗️ Architecture & Project Structure

The application is structured into distinct layers to separate presentation, business logic, configuration, and core utilities.

```text
Premiere Companion/src/
├── Premiere Companion.pyw   # 🚀 Main Entry Point (Admin checks, single-instance lock, UI init)
├── Core/                    # ⚙️ System & Infrastructure
│   ├── server.py            # Asyncio WebSocket server (bridge to Premiere Pro plugin)
│   ├── hotkeys.py           # Win32 global hotkey listener & dispatcher
│   ├── theme_qss.py         # Dynamic PyQt6 stylesheet (QSS) generator
│   └── paths.py             # Global path resolution utility
├── Data/                    # 💾 Configuration & User Data (State)
│   ├── keybinds.json        # User-defined shortcuts
│   ├── rules.json           # Application specific rules/logic states
│   └── theme.json           # User-customizable theme definitions
├── GUI/                     # 🖥️ Presentation Layer (PyQt6)
│   ├── Pages/               # Main views (EffectsPage, SettingsPage, etc.)
│   └── Widgets/             # Reusable UI components (SearchBar, Menu, ItemList)
├── Modules/                 # 🎬 Premiere Pro Interaction Logic
│   ├── apply_effect.py      # Logic & input simulation to apply effects in Premiere
│   ├── apply_preset.py      # Logic & input simulation for presets
│   ├── fetch_effects.py     # Data retrieval modules
│   └── SearchBar.py         # Core search engine logic
└── Assets/                  # 🎨 Resources (Icons, SVGs, Fonts)
```

### 1. Entry Point & Lifecycle (`Premiere Companion.pyw`)
- **Initialization:** Handles administrative elevation checks and enforces a single-instance policy via `premiere_companion.lock`.
- **Environment Setup:** Configures a centralized `__pycache__` and dynamically applies the QSS theme before rendering the splash screen. 
- *Team Note:* When modifying startup behavior, always ensure the splash screen and single-instance locks are gracefully handled to prevent ghost processes.

### 2. Core Infrastructure (`Core/`)
- **`server.py`:** **CRITICAL COMPONENT.** This runs an `asyncio` WebSocket server on a separate `QThread`. The Adobe Premiere Pro extension connects *to this server* as a client. This is our primary communication bridge.
- **`hotkeys.py`:** Bypasses standard PyQt input handling to use Win32 global hotkeys, allowing the app to listen for triggers even when Premiere Pro is the active window in the foreground.
- **`theme_qss.py`:** Our dynamic theme engine. It parses JSON configurations and generates QSS on the fly.

### 3. Data & Configuration Layer (`Data/`)
- State and configuration are strictly separated from logic. All user preferences, theme definitions, and app states live here in JSON format.
- *Why?* This makes user data backup trivial and allows users to share custom themes or rule sets easily. 

### 4. Premiere Integration Layer (`Modules/`)
- This is where our app interfaces with Premiere Pro, often utilizing low-level OS inputs or dispatching commands via the WebSocket server.
- Modules like `apply_effect.py` use `ctypes` and `pyautogui` to ensure modifier keys (Ctrl, Shift, Alt) are correctly simulated or released when executing macros inside Premiere.
- *Team Note:* Keep UI logic completely out of this folder. If a module needs to update the UI, use PyQt Signals (`pyqtSignal`) emitted from a worker thread.

### 5. Presentation Layer (`GUI/`)
- Built entirely with PyQt6, structured to maximize component reusability.
- **`Pages/`**: The main modular views. Each page focuses strictly on layout and bridging user actions to `Modules/` or `Core/`.
- **`Widgets/`**: Reusable UI components. If you build a custom UI element, it belongs here.

---

## 🚀 Development Workflows & Conventions

### Adding a New Feature
1. **Data Model First:** If your feature requires saving state, define its structure in `Data/`. Update `Core/paths.py` if necessary.
2. **Business Logic:** Write the core interaction logic in `Modules/`. If it requires communicating with Premiere, utilize the `send_to_plugin()` method exposed by `Core/server.py`.
3. **UI Implementation:** Create or update the relevant Page in `GUI/Pages/`. Connect UI events to your module via PyQt slots and signals.
4. **Theming:** Drive all new styling via `Core/theme_qss.py` and `Data/theme.json`. **Do not hardcode colors** in the Python UI code.

### Modifying the Theme Engine
When tweaking the UI's look, always update `Data/theme.json`. The ultimate goal is that a user could completely redesign the app's aesthetic purely by editing the JSON file.

### Debugging Premiere Communication
Pay special attention to `Core/server.py`. Because we act as the server, network/socket timeouts or extension connection issues will surface here. If Premiere isn't responding, ensure the `websockets` loop is running and that the Premiere CEP/ExtendScript client successfully negotiated the connection.

### Handling Windows Inputs
If you add new macros or automation (in `Modules/`), be hyper-aware of the user's keyboard state. Use the `force_release_modifiers()` methods (found in `apply_effect.py`) to prevent stuck keys during automated `pyautogui` sequences.

