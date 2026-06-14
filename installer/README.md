# Valorant Tracker Installer

This folder contains the Inno Setup installer script for the Windows desktop app.

## Prerequisites

1. Build the app executable first:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_exe.ps1
```

2. Install Inno Setup 6.

3. Optional but recommended: place the Microsoft Edge WebView2 Evergreen Bootstrapper here:

```text
installer/dependencies/MicrosoftEdgeWebView2Setup.exe
```

If the bootstrapper is present, the installer runs it silently when WebView2 is missing. If it is absent, the installer still builds and shows a warning on machines where WebView2 is not detected.

## Build Installer

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_installer.ps1
```

Build both exe and installer:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_installer.ps1 -BuildExe
```

Output:

```text
installer/output/ValorantTrackerSetup.exe
```

## Install Behavior

- Installs per-user into `%LOCALAPPDATA%\Programs\ValorantTracker`.
- Creates Start Menu shortcuts.
- Optionally creates a desktop shortcut.
- Creates `%APPDATA%\ValorantTracker`, `%APPDATA%\ValorantTracker\logs`, and `%APPDATA%\ValorantTracker\cache`.
- Does not delete `%APPDATA%\ValorantTracker` on uninstall.
- Removes the app's Windows startup entries on uninstall:
  - `ValorantTracker`
  - `ValorantTrackerValorantWatcher`
