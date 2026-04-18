# 🎯 Better Motion
[![](https://img.shields.io/badge/←_📖_Guides-30363d?style=for-the-badge)](../README.md#-📖-Guides)

Better Motion lets you adjust Premiere Pro's Motion properties — **Position, Scale, Rotation, Opacity** — directly from your keyboard, without clicking inside Premiere's Effect Controls panel.

Two interaction styles:
- **Interactive overlay** — a hotkey opens a fullscreen overlay; drag the mouse to adjust, click to confirm
- **Inline command** — type a value in the search bar (`/BM scale 85`) and it applies immediately with no overlay

---

## Better Transform

**Better Transform** is an all-in-one overlay that handles Position, Rotation, and Scale in a single session — just by holding different mouse buttons.

| Mouse state | Property being adjusted |
|---|---|
| No button held | Position |
| Hold **Right Mouse Button** | Rotation |
| Hold **Middle Mouse Button** | Scale |
| Click **Left Mouse Button** | Confirm current property and exit |

When you switch from one button to another, the current property is **committed immediately** before the next one begins. Each switch is a separate undo step in Premiere.

Bind a hotkey to **Better Transform** in **Settings → Better Motion** to trigger it from anywhere.

---

## Per-Property Hotkeys

Each property has its own set of assignable hotkeys:

| Action | What it does |
|---|---|
| **Adjust** | Opens the interactive overlay for that property |
| **Reset** | Resets the property to Premiere Pro's default value |
| **Add** | Instant nudge forward by the configured amount |
| **Sub** | Instant nudge backward by the configured amount |

**Position** has separate X and Y controls:

| Action | Axis |
|---|---|
| X Add / X Sub | Horizontal (left / right) |
| Y Add / Y Sub | Vertical (up / down) |

**Scale, Rotation, Opacity** each have a single Add/Sub pair.

---

## Interactive Overlay

When an **Adjust** hotkey fires (or you select a BM command from the search bar without an inline value):

1. A fullscreen overlay appears — the cursor is hidden and input is captured
2. The current property value is read from Premiere Pro and displayed
3. **Move the mouse** to change the value — the overlay shows `current → new` in real time
4. **Click** (LMB) to confirm, **Esc** to cancel and restore the original value

### Modifier keys

Hold these while dragging to control sensitivity:

| Key | Speed |
|---|---|
| _(none)_ | 1× — normal |
| **Shift** | 2× — faster, coarse adjustment |
| **Ctrl** | 0.25× — slower, precision |

### Mouse Axis

For Scale, Rotation, and Opacity, choose which mouse movement drives the value:

| Axis | Movement |
|---|---|
| **Horizontal** | Left/right mouse movement |
| **Vertical** | Up/down mouse movement |

The **Invert** checkbox flips the direction. Configure per property in **Settings → Better Motion**.

> Position always uses X=horizontal and Y=vertical — no axis config needed.

---

## Live Motion

When **Live Motion** is enabled, changes appear in Premiere Pro's Program Monitor in real time as you drag.

> ⚠️ **Undo warning:** Each incremental update is a separate undo step. Undoing a Live Motion adjustment requires pressing `Ctrl+Z` multiple times. Use the **Reset** hotkeys as a faster alternative.

Toggle in **Settings → Better Motion → Enable Live Motion**.

---

## Inline Commands (Search Bar)

Better Motion properties can be controlled directly from the search bar without opening any overlay. See [Commands → Better Motion Commands](Commands.md#better-motion-commands-bm) for full syntax.

Quick reference:

| Search input | Result |
|---|---|
| `/BM scale 85` | Set scale to 85 |
| `/BM opacity +10` | Add 10 to current opacity |
| `/BM rotation -15` | Subtract 15 from rotation |
| `/BM position 960.540` | Set position to X=960, Y=540 |
| `/BM scale reset` | Reset scale to default |

---

## Setup

1. Go to **Settings → Better Motion**
2. Enable Better Motion with the toggle at the top
3. Bind a hotkey to **Better Transform** for the all-in-one mode
4. Bind **Adjust**, **Reset**, **Add**, **Sub** hotkeys per property as needed
5. Set nudge **amounts** for Add/Sub (e.g., Position X Add = 50 px, Scale Add = 10)
6. Configure **Mouse Axis** and **Invert** per property
7. Optionally enable **Live Motion**
8. Click **Save Configuration**

> ℹ️ Better Motion hotkeys are conflict-checked against the search bar key and all custom hotkeys. Duplicates are rejected on save.

---

## Examples

### Example 1 — Nudge a clip 50 px right (instant, no overlay)

Bind `Position → X Add` to `Ctrl+Right` with amount `50`.

Press `Ctrl+Right` with a clip selected → position shifts +50 px on X instantly.

---

### Example 2 — Fine-tune opacity with precision

Bind `Opacity → Adjust` to `Alt+O`.

1. Select a clip in Premiere
2. Press `Alt+O` → overlay opens, showing current opacity
3. Hold **Ctrl** (0.25× speed) and move the mouse slowly
4. Click to confirm the value

---

### Example 3 — Full Better Transform session

Bind `Better Transform` to `Alt+T`.

1. Select a clip
2. Press `Alt+T` → overlay opens in **Position** mode
3. Drag to reposition the clip
4. Hold **RMB** → switches to **Rotation** mode; drag to rotate
5. Hold **MMB** → switches to **Scale** mode; drag to resize
6. Click **LMB** → confirms Scale and exits

Each mode switch commits that property as a separate undo step.

---

### Example 4 — Reset position from the search bar

```
Ctrl+Space  →  /BM position reset  →  Enter
```

Position resets to Premiere's default (960, 540 for 1080p) with no overlay.

---

### Example 5 — Set exact position in one command

```
Ctrl+Space  →  /BM position 0.0  →  Enter
```

Sets X=0, Y=0. The `.` separates X and Y values.

---

### Example 6 — "Reset Transform" macro

Create a macro with these actions:

| # | Action | Value |
|---|---|---|
| 1 | Position | `reset` |
| 2 | Scale | `reset` |
| 3 | Rotation | `reset` |
| 4 | Opacity | `reset` |

Run: `Ctrl+Space → Reset Transform → Enter` — all four properties snap to defaults in one shot.

---

### Example 7 — Nudge scale on multiple clips with keyboard only

Bind `Scale → Add` to `=` (amount: 10) and `Scale → Sub` to `-` (amount: 10).

Select clips, tap `=` or `-` to nudge scale in real time — no overlay, no mouse. Each tap is a separate undo step.

_Back to [Guides](../README.md#-📖-Guides)_
