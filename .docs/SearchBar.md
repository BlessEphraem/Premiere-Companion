# 🔍 Search Bar

[![](https://img.shields.io/badge/←_📖_Guides-30363d?style=for-the-badge)](../README.md#-📖-Guides)

## Opening & Closing the Search Bar

|Action|Default Shortcut|
|---|---|
|Open search bar|`Ctrl+Space` _(while Premiere Pro is focused)_|
|Close search bar|`Escape` _(or any click outside of it)_|
|Close on focus loss|Automatic — the bar closes if you click outside it|

To change theses, go to **Settings -> Search -> Bar**.
> The trigger shortcut is fully configurable. Go to **Settings -> Search -> Bar** in the app and change the **"Run Search Bar"** binding to whatever you prefer.

> ⚠️ The shortcut only triggers when **Adobe Premiere Pro is the active window**. It will not interfere with other applications.

## The Interface

When opened, the search bar displays:

```
┌────────────────────────────────────────────┐
│  Search (All)...                           │
├────────────────────────────────────────────┤
│  [Recent]      Cross Dissolve              │
│  [Preset]      My Color Grade              │
│  [FxVideo]     Lumetri Color               │
│  [Transition]  Film Dissolve               │
│  ...                                       │
└────────────────────────────────────────────┘
```

Each result shows a **colored type tag** on the left and the **effect name** on the right.

### Tag Colors

|Tag|Meaning|
|---|---|
|`[Recent]`|One of your 3 most recently applied items|
|`[FxVideo]`|Video effect|
|`[FxAudio]`|Audio effect|
|`[Transition]`|Video or audio transition|
|`[Preset]`|A saved preset from your Premiere Pro library|

## Typing & Searching

Start typing immediately after opening the bar — there's no need to click into the input field, it is focused automatically.

- The search matches against **all words in the effect name**, in any order. Typing `blur fast` will match `Fast Blur` or `Camera Blur Fast`.
- Up to **75 results** are displayed at a time, ranked by relevance.
- **Recently used items** always appear at the top, regardless of query.

## Keyboard Navigation

You never need to touch the mouse to use the search bar.

|Key|Action|
|---|---|
|`↑` / `↓`|Move selection up/down through results|
|`CTRL + ←`|Switch to previous category filter|
|`CTRL + →`|Switch to next category filter|
|`Enter`|Apply the selected result|
|`Escape`|Close the search bar|

## Category Filtering

Use `←` / `→` when your cursor is at the beginning or end of the input field to cycle through categories. The placeholder text in the search box updates to reflect the active filter.

|Category|Shows|
|---|---|
|**All**|Everything — effects, transitions, presets|
|**FxVideo**|Video effects only (no transitions)|
|**FxAudio**|Audio effects only (no transitions)|
|**Transition**|Video and audio transitions only|
|**Preset**|Saved presets only|
|**Commands**|Specific commands and custom user macro.|

This is useful when you know the type of element you're looking for and want to narrow down a long results list.

## Applying Effects & Audio Effects

Select the desired item with `↑` / `↓` and press `Enter`.

The app will:

1. Bring Premiere Pro to the foreground
2. Send the effect's internal match name to the plugin via WebSocket
3. The plugin applies the effect to the currently selected clip(s) on the timeline

No mouse interaction required.

## Applying Transitions

Transitions require an extra step: choosing how the transition is applied to the clip edge.

After selecting a transition and pressing `Enter`, the bar switches to **alignment selection mode**:

```
┌──────────────────────────────────────┐
│  Choose alignment (Enter to apply)   │
├──────────────────────────────────────┤
│  <  At Start                         │
│  >  At End                           │
│  =  Both                             │
└──────────────────────────────────────┘
```

|Option|Behavior|
|---|---|
|**At Start**|Applies the transition to the beginning of the clip|
|**At End**|Applies the transition to the end of the clip|
|**Both**|Applies the transition to both edges|

Use `↑` / `↓` to select the alignment, then press `Enter` to confirm. Press `Escape` to go back and search again.

## Applying Presets (Quick Apply)

> Requires **Quick Apply** to be configured and enabled. See the [main README](../README.md).

When Quick Apply is enabled, selecting a preset and pressing `Enter` triggers the following automated sequence:

1. Premiere Pro is brought to the foreground
2. The Effects panel is opened (`Shift+2` by default)
3. The search box inside Premiere is focused (`Shift+F` by default)
4. The preset name is pasted into the search box
5. The mouse moves to the calibrated preset icon position
6. A drag-and-drop begins from the preset icon toward your original cursor position
7. You release the mouse over your clip to drop the preset

> ℹ️ During step 7, **you must move the mouse to the target clip and release** — the app initiates the drag but you control where the preset lands. This is intentional, as Premiere Pro requires an actual drag-and-drop to apply presets.

If Quick Apply is **disabled**, selecting a preset will simply display a confirmation in the app's console log without doing anything in Premiere Pro. Enable it in **Settings** first.

## Recent Items

The search bar remembers your **3 most recently applied** effects, transitions, and presets. These always appear at the top of results with a `[Recent]` tag, even when the search field is empty — making it trivial to re-apply your most used items.

Recent history is saved to `Data/search_history.json` and persists across sessions.

## Tips & Best Practices

- **Leave the search field empty and press `Enter`** — the first result (most recently used item) will be applied immediately. Great for repeat applications.
- **Use category filters** (`CTRL + ←` / `CTRL + →`) when you have a long list and know what type you need.
- **Keep Premiere Pro's window position stable** if you use Quick Apply. Moving or resizing the Premiere window invalidates the calibration and requires you to re-run the setup wizard.
- **Name your presets descriptively** — since Quick Apply searches for an exact name, unique and descriptive preset names make targeting much more reliable.
- If a transition or effect name looks garbled (e.g., `AE.ADBE XYZ PrTr`), go to the **Regex Cleaner** page and run **Auto-Generate Rules** to clean them up.



---

## Examples

### Example 1 — Instant re-apply (empty field)

```
Ctrl+Space  →  Enter
```

No typing needed. The most recently used item is pre-selected and applies immediately. Great for repeating the same effect across multiple clips.

---

### Example 2 — Find and apply a video effect

```
Ctrl+Space  →  gaussian  →  ↓ (select Gaussian Blur)  →  Enter
```

The effect is applied to all selected clips on the Premiere timeline.

---

### Example 3 — Apply a transition to the end of a clip

```
Ctrl+Space  →  cross dissolve  →  Enter  →  ↓ (select "At End")  →  Enter
```

After selecting a transition, the bar switches to alignment mode. Use ↑/↓ to pick **At Start**, **At End**, or **Both**, then confirm with Enter.

---

### Example 4 — Filter to presets only before searching

```
Ctrl+Space  →  CTRL+→ (switch to Preset)  →  my grade  →  Enter
```

Cycling to the **Preset** category first narrows a long list to only your saved presets.

---

### Example 5 — Apply a preset via keyword

```
Ctrl+Space  →  /P my grade  →  Enter
```

Same result as Example 4, but typed in one motion using the `/P` keyword prefix.

---

### Example 6 — Run a Better Motion command inline

```
Ctrl+Space  →  /BM scale 85  →  Enter
```

Sets the selected clip's scale to 85 without opening any dialog. See [Commands](Commands.md) for full BM syntax.

---

### Example 7 — Run a macro

```
Ctrl+Space  →  Quick Grade  →  Enter
```

Macros appear in search like any other item. No category filter needed — just type the macro name.

---

### Example 8 — Re-apply a recent item with keyboard only

```
Ctrl+Space  →  ↓ (select [Recent] item)  →  Enter
```

Recent items are pinned at the top even with an empty query. No typing — just arrow key and Enter.

_Back to [README](../README.md)_