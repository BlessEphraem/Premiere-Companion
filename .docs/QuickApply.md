# ⚡ How to Enable 'Quick Apply' (Apply Presets)
Quick Apply lets you apply your saved Premiere Pro presets directly from the search bar, using screen capture and hardware-level mouse/keyboard simulation.

## How it works
Quick Apply works by recording the **exact screen position** of a preset icon in Premiere Pro's effect browser. When you apply a preset from the search bar, the app automatically:

1. Opens the Effects panel
2. Types the preset name in the search box
3. Drags the preset from its recorded position to your timeline cursor
For this to work reliably, **all your presets must be stored at the same folder depth** in Premiere Pro's preset browser, so that a search always returns exactly one result at a consistent screen position.

## Setup Steps
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