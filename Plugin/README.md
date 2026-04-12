# 🔌 Premiere Companion (Listener) — UXP Plugin

This is the UXP plugin component for **Premiere Companion**. It acts as the communication bridge between Adobe Premiere Pro and the Premiere Companion desktop application.

> ⚠️ **This plugin has no standalone use.** It is a dependency of [Premiere Companion](https://github.com/BlessEphraem/Premiere-Companion) and does nothing on its own without it.

## 📋 Prerequisites

- **Adobe Premiere Pro 25.6.1 or later**, or a **Beta version** with UXP plugin support enabled. Earlier versions do not support UXP plugins and are not compatible.
- **Adobe Creative Cloud** must be installed and running on your machine. As long as Creative Cloud is present, the installer should be able to register the plugin correctly.

---

## 🚀 Installation

1. Download the latest [release](https://github.com/BlessEphraem/Premiere-Companion-UXP/releases).
    > ⚠️ **Note on cloning:** I highly recommend downloading the release instead of cloning the repository. If you want to edit the plugin, simply download the release and import it directly into the **Adobe UXP Developer Tool**.
2. **Do not move any files.** The `.bat` installer must remain in the same folder as the `.ccx` plugin file, or it will not find it.
3. Right-click the `update_ccx.bat` file and run it **as Administrator**.

The script will automatically locate the Adobe plugin installer and register the plugin with Premiere Pro. No further steps are required.

## 🛠️ Troubleshooting

### The script fails or nothing happens

**First, make sure you ran the `.bat` as Administrator.** This is the most common cause of failure. Right-click → *Run as administrator*.

### The plugin still doesn't appear in Premiere Pro

The installer relies on Adobe's `UnifiedPluginInstallerAgent.exe`, which is deployed as part of the Creative Cloud suite. As long as the **AdobeUpdateService** Windows service is running, this agent should be present and functional.

To verify:
1. Press `Win+R`, type `services.msc`, and hit Enter.
2. Look for **AdobeUpdateService** in the list.
3. Make sure its status is **Running**. If it isn't, start it and re-run the `.bat`.

### `UnifiedPluginInstallerAgent.exe` is not found

If the script reports that it cannot locate `UnifiedPluginInstallerAgent.exe`, your Adobe installation may be in a non-standard path. You'll need to find the file manually and update the path in the `.bat` accordingly.

A tool like **[Everything](https://www.voidtools.com/)** (free, instant file search) makes this trivial — just search for `UnifiedPluginInstallerAgent.exe` and it will find it immediately regardless of where Adobe installed it.

Once located, open the `update_ccx.bat` file in a text editor, update the path on the relevant line, save, and re-run as Administrator.

---

*Once installed, head back to [Premiere Companion](https://github.com/BlessEphraem/Premiere-Companion) to complete the setup.*

## 📄 License

GPL-3.0 license — see [LICENSE](LICENSE) for details.

