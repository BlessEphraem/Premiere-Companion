# 🕹️ Commands

[![](https://img.shields.io/badge/←_📖_Guides-30363d?style=for-the-badge)](../README.md#-📖-Guides)

Commands are special items in the search bar's `[Commands]` category. They give you direct control over the app — toggling features, running transforms, executing macros — without leaving your keyboard.

---

## Command Keywords

Keywords are **prefix shortcuts** you type in the search bar to instantly filter results to a specific category.

| Keyword | Default | Filters to |
|---|---|---|
| `/` | `/` | All effects, transitions, presets |
| `/V` | `/V` | Video effects only |
| `/A` | `/A` | Audio effects only |
| `/T` | `/T` | Video transitions only |
| `/P` | `/P` | Presets only |
| `/QA` | `/QA` | Quick Apply control commands |
| `/BM` | `/BM` | Better Motion transform commands |

### Using keywords

Type the keyword directly in the search bar — the category filter switches automatically and the list narrows.

```
/V            → show all video effects
/V blur       → video effects matching "blur"
/BM           → show Better Motion commands
/QA           → show Quick Apply commands
```

### Configuring keywords

Go to **Settings → Search → Commands** to rename any keyword. The `/` separator is always prepended — you only define the letter(s) after it.

> ⚠️ Keywords must be unique. The app rejects duplicates and will not save conflicting prefixes.

---

## Quick Apply Commands (`/QA`)

These commands appear once Quick Apply has been calibrated (a mouse position capture exists).

| Command | What it does |
|---|---|
| `Toggle Quick Apply (ON / OFF)` | Enable or disable Quick Apply instantly |
| `Set Delay (N ms)` | Change the preset-application delay |
| `Start Calibration` | Re-run the 5-second calibration countdown |

---

## Better Motion Commands (`/BM`)

These commands appear when Better Motion is enabled.

| Command | What it does |
|---|---|
| `Better Transform` | Open the full interactive Better Motion overlay |
| `Position` | Set or adjust clip position (X and/or Y) |
| `Scale` | Set or adjust clip scale |
| `Rotation` | Set or adjust clip rotation |
| `Opacity` | Set or adjust clip opacity |

### Inline value syntax

Type a value **after** the command name to apply it without opening a dialog:

| Input | Meaning |
|---|---|
| `50` | Set to 50 (absolute) |
| `+10` | Add 10 to current value |
| `-5` | Subtract 5 from current value |
| `reset` | Reset property to its default |

**Position only** — control X and Y independently with a `.` separator:

| Input | X | Y |
|---|---|---|
| `100.200` | Set X=100 | Set Y=200 |
| `.500` | (unchanged) | Set Y=500 |
| `100.` | Set X=100 | (unchanged) |
| `+50.-20` | Add 50 to X | Subtract 20 from Y |

> ℹ️ Use `,` as the decimal separator for fractions (e.g. `100,5` = 100.5).

---

## Macros as Commands

Every macro you create appears automatically in the Commands category with a `[CMD.MA]` type tag. Type its name in the search bar to run it. See [Macros & Hotkeys](MacrosAndHotkeys.md) for how to create them.

---

## Examples

### Example 1 — Filter to video effects and apply one

```
/V gaussian
```

Opens the search bar, filters to video effects, selects "Gaussian Blur", applies it to the selected clip.

---

### Example 2 — Set opacity to 80 (absolute)

```
/BM opacity 80
```

Sets the selected clip's opacity to exactly 80. No dialog opens.

---

### Example 3 — Nudge position right by 50 px, leave Y unchanged

```
/BM position +50.
```

Adds 50 to X. The trailing `.` signals "skip Y".

---

### Example 4 — Set position to (960, 540) in one command

```
/BM position 960.540
```

Sets X=960, Y=540 simultaneously.

---

### Example 5 — Toggle Quick Apply off from the search bar

```
/QA Toggle Quick Apply
```

No need to open settings. The command label updates to show the new state immediately.

---

### Example 6 — Re-calibrate without opening settings

```
/QA Start Calibration
```

Triggers the 5-second countdown. Move your mouse over the preset icon in Premiere Pro before time runs out.

[![](https://img.shields.io/badge/←_📖_Guides-30363d?style=for-the-badge)](../README.md#-📖-Guides)

_Back to [Guide](../README.md#-📖-Guides)_
