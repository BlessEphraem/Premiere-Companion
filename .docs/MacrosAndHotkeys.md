# 🔁 Macros & Hotkeys
[![](https://img.shields.io/badge/←_📖_Guides-30363d?style=for-the-badge)](../README.md#-📖-Guides)

## Macros

A macro is a **named sequence of actions** that executes step by step, automatically. Run any macro from the search bar or bind it to a hotkey for single-keypress execution.

### Creating a Macro

1. Go to **Macros** in the sidebar
2. Click **+ New Macro**
3. Enter a macro name
4. Search for actions in the editor and add them in order
5. Click **Save Macro**

The macro appears immediately in the search bar under `[Commands]`.

---

### Action Types

| Type | Description | Configurable param |
|---|---|---|
| `[FxVideo]` | Apply a video effect to the selected clip | — |
| `[FxAudio]` | Apply an audio effect to the selected clip | — |
| `[Transition]` | Apply a transition to the selected clip edge | Alignment |
| `[Preset]` | Apply a preset via Quick Apply | — |
| `[CMD.BM.*]` | Set a Better Motion transform property | Value |
| `SLEEP` | Pause N milliseconds before the next action | Duration (ms) |

---

### Transition Alignment

When a transition is added to a macro, you choose where it attaches:

| Option | Behavior |
|---|---|
| At Start | Applied to the beginning of the clip |
| At End | Applied to the end of the clip |
| Both Sides | Applied to both edges |

Click the **✎ edit** button on the transition action to change alignment at any time.

---

### Better Motion Values

BM actions require a value set at creation time. The dialog opens automatically when you add one.

| Value | Meaning |
|---|---|
| `50` | Set to 50 (absolute) |
| `+10` | Add 10 to current value |
| `-5` | Subtract 5 |
| `reset` | Reset property to default |
| `100.200` | Position only — set X=100, Y=200 |
| `.500` | Position only — set Y=500, skip X |
| `+50.-20` | Position only — add 50 to X, subtract 20 from Y |

Click the **✎ edit** button on a BM action to update its value later.

---

### SLEEP

Inserts a deliberate pause between two actions. Click **Add Sleep** in the editor and set a duration (1 – 30,000 ms).

> ℹ️ A fixed **500 ms gap** is automatically inserted between every non-SLEEP action. Add a SLEEP only when Premiere Pro needs extra time to react (e.g., after opening a panel or applying a heavy effect).

---

### Reordering and Editing Actions

Each action row has:
- **↑ / ↓** buttons — reorder the action in the sequence
- **✕** button — remove the action
- **✎ edit** button — change params (transitions, BM commands, SLEEP only)

---

### Pre-flight Validation

Before a macro starts, the app validates all dependencies:

| If macro contains | Requirement |
|---|---|
| Any `[Preset]` action | Quick Apply must be calibrated **and** enabled |
| Any `[CMD.BM.*]` action | Better Motion must be enabled |

If any check fails, the macro is **blocked entirely** — no actions run. An error is logged in the console.

---

### Editing and Deleting

On the **Macros** page, each macro row has **Edit** and **Delete** buttons. Editing reopens the Macro Editor with all existing actions pre-loaded.

---

## Custom Hotkeys

A custom hotkey binds a **keyboard shortcut** to any effect, preset, or macro. The shortcut fires immediately while **Adobe Premiere Pro is the active window** — no search bar needed.

### Adding a Hotkey

1. Go to **Macros → Custom Hotkeys**
2. Click the key capture field and press the desired key combination
3. Search for the effect, preset, or macro to bind
4. Click **Add**

Hotkeys are stored in `Data/keybinds.json` and activate immediately on save.

### Conflict Detection

The app checks every new hotkey against:
- All existing custom hotkeys
- The search bar trigger key
- Better Motion hotkeys

If a conflict is found, the hotkey is rejected. Choose a different combination.

### Removing a Hotkey

Click **✕** on any row in the Custom Hotkeys list.

---

## Examples

### Example 1 — "Quick Grade" macro (color effect + wait + preset)

**Goal:** Apply Lumetri Color, wait for Premiere to register it, then apply a motion preset.

| # | Action | Type | Param |
|---|---|---|---|
| 1 | Lumetri Color | `[FxVideo]` | — |
| 2 | Sleep | `SLEEP` | 800 ms |
| 3 | My Motion Preset | `[Preset]` | — |

Run: `Ctrl+Space → Quick Grade → Enter`

---

### Example 2 — "Reset Transform" macro

**Goal:** Reset position, scale, and rotation to their defaults in one action.

| # | Action | Type | Param |
|---|---|---|---|
| 1 | Position | `[CMD.BM.position]` | `reset` |
| 2 | Scale | `[CMD.BM.scale]` | `reset` |
| 3 | Rotation | `[CMD.BM.rotation]` | `reset` |

Run: `Ctrl+Space → Reset Transform → Enter`

---

### Example 3 — "Center + Scale Up" macro

**Goal:** Set clip to screen center and scale to 110 in one shot.

| # | Action | Type | Param |
|---|---|---|---|
| 1 | Position | `[CMD.BM.position]` | `960.540` |
| 2 | Scale | `[CMD.BM.scale]` | `110` |

---

### Example 4 — Transition on both ends

**Goal:** Apply Cross Dissolve to both edges of the selected clip.

| # | Action | Type | Param |
|---|---|---|---|
| 1 | Cross Dissolve | `[Transition]` | Both Sides |

Single Enter press — both edges get the transition.

---

### Example 5 — Custom hotkey for Cross Dissolve

1. Go to **Macros → Custom Hotkeys**
2. Capture key: `Ctrl+D`
3. Search: `Cross Dissolve`
4. Click **Add**

`Ctrl+D` with Premiere Pro active now applies Cross Dissolve instantly.

---

### Example 6 — Custom hotkey to run a macro

1. Create macro `"Color Stack"`
2. Go to **Custom Hotkeys** → capture `Ctrl+Shift+G`
3. Search: `Color Stack` (shows up under Commands)
4. Click **Add**

`Ctrl+Shift+G` → entire macro runs. No search bar, no mouse.

_Back to [Guides](../README.md#-📖-Guides)_
