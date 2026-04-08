# Roadmap - Premiere Companion

## Hard Limits (API Limitations)

> ***Why can't I apply an audio transition?***
- The Premiere Pro UXP API does not support it at this time.

---

## Known Issues

- **Preset Quick Apply breaks if Premiere is moved/resized** - calibration stores absolute window coordinates. If the user moves or resizes Premiere between calibration and use, the apply will fail and ask for recalibration.

---

## Work In Progress

- [ ] **Custom Commands (Macros)** - Allow users to create named sequences of Premiere Pro commands (nest, rename, label, export, etc.) without writing code. These would appear as `[CMD]` items in the main list.

  *Planned command categories:*
  - Global: Undo
  - Timeline: Nest, Speed, Duration, Trim, Move, Clip Labels, Keyframes
  - Selection: Select Above/Below, Extend, Invert
  - Export: In/Out, Full Sequence, Selected Clips, Frame, Frames at Markers
  - Project: Increment & Save, Change Workspace, Execute Script
  - Preferences: Snap, Linked Selection, Show Rulers/Guides, etc.

- [ ] **Relative Preset Calibration** - Replace absolute window coordinate storage with relative (% of window size) so Quick Apply survives window moves and minor resizes without recalibration.

- [ ] **Preset Type Detection** - Detect whether a preset is a transition, effect, audio, or keyframed. Would allow Quick Apply to be smarter (e.g., only auto-apply on keyframed presets).

---

## To Do

- [ ] **Search Performance** - Preset search can be slow on large libraries. Needs optimization (indexing or debounce improvements).

- [ ] **Utils: Debug & Developer Tools** - See `Utils/` folder. Planned tools include connection inspector, config viewer, regex tester, hotkey conflict detector, and the page scaffold generator.

---

## Ideas & Backlog

- FFMPEG integration for local export/processing?
- Mac version (would require replacing all `win32` / Windows API calls)
- Better Premiere Hotkeys: auto-detect and mirror Group/Ungroup and other dual-action hotkeys

---

## Done

- [x] **Better Motion Stability & Precision** - Fixed Premiere freezing ("Not Responding") with an intelligent frame-skipping lock. Optimized update frequency to 20 FPS and added support for keyframes in "Direct" (Add/Sub) and "Reset" modes.
- [x] **Addons Page Refactor** - Consolidated Addons (Keymaps) and Settings. Moved "Run Search Bar" hotkey to SearchBar config and added Premiere Keybinds access directly into the Quick Apply card.
- [x] **Search Keywords Config** - Users can now configure or disable search command prefixes (`/V`, `/A`, `/T`, `/P`, `//`) via a dedicated UI in Settings.
- [x] **Priority / Ignore List** - Full management UI to hide specific effects/presets or pin them to the top of results.
- [x] **Dynamic Icon Management** - Application logo and navigation icons now react to the active state (colorized vs subtle grey) for better visual feedback.
- [x] **Complete UI Rework** - Full redesign with a `GUI/Pages/` + `GUI/Widgets/` architecture. Main window, Settings, Hotkeys, Theme, RegEx, Better Motion, Quick Apply, Search Bar config pages all implemented.
- [x] **Dynamic Theme System** - 40+ customizable colors/sizes/fonts stored in `theme.json`, applied via generated QSS. Full theme editor UI in `GUI/Pages/theme_page.py`.
- [x] **Floating Search Bar** - Global overlay (Ctrl+Space) with blur, opacity config, filter cycling, recent history, and quick-apply shortcut. (`GUI/Widgets/SearchBar.py`)
- [x] **Better Motion Overlay** - Real-time mouse-driven adjustment of position, scale, rotation, and opacity via WebSocket.
- [x] **Effect Type Labels** - FX.V, FX.A, TR.V, PRST labels with color coding, configurable in `Core/configs/labels_config.py`.
- [x] **RegEx Rules Editor** - User-editable rules with Auto-Generate from transition names. (`GUI/Pages/regex_page.py`)
- [x] **Configure Premiere Pro** - Port settings (WS + TCP), auto-connect toggle, version detection. (`GUI/Pages/premiere_page.py`)
- [x] **Premiere Keybinds Retrieval** - Retrieve and store essential Premiere keybinds. (`GUI/Pages/premiereKeybinds_page.py`)
- [x] **Custom Hotkeys** - Assign any effect/preset to a global keyboard shortcut. (`GUI/Pages/customHotkey_page.py`)
- [x] **Quick Apply (Preset Automation)** - Calibration wizard + automated keybind+mouse sequence to apply presets. (`Modules/apply_preset.py`, `GUI/Pages/quickApply_page.py`)
- [x] **Import / Export** - Export and import all `Data/` configs as a ZIP via the UI.
- [x] **Chunked Effect Sync** - Effects received in chunks from the Premiere plugin to avoid timeouts on large libraries.
- [x] **Single Instance + UAC** - Lock file enforcement and automatic admin elevation on launch.     
- [x] **Utils: scaffold_page.py** - Interactive CLI generator for new pages, widgets, and features, following all project conventions.
