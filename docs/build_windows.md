# Windows EXE Build

Build output target:

```text
dist/ValorantTracker/ValorantTracker.exe
```

## Prerequisites

Install/update the project dependencies:

```powershell
.\venv\Scripts\python.exe -m pip install -r .\requirements.txt
```

This installs `pywebview` and `pyinstaller`.

## Build

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_exe.ps1
```

The build script:

- uses `valorant_tracker.spec`;
- bundles `desktop_main.py`;
- includes `templates/`, `static/`, and `data/predict_trs_generated.py`;
- excludes `.env`, `tracker.db`, logs, debug JSON, snapshots, and calibration/OCR tooling;
- writes runtime data to `%APPDATA%\ValorantTracker`, not the install folder.

## Dev Checks

Run the desktop launcher before building:

```powershell
.\venv\Scripts\python.exe .\desktop_main.py
```

Run the browser dev mode:

```powershell
.\venv\Scripts\python.exe .\desktop_main.py --dev
```

Run the Valorant startup watcher manually:

```powershell
.\venv\Scripts\python.exe .\desktop_main.py --watch-valorant
```

The Settings toggles manage these per-user Windows startup entries:

- `ValorantTracker`: launch the app on Windows login.
- `ValorantTrackerValorantWatcher`: wait for VALORANT, then launch the app.

## Build Installer

Install Inno Setup 6, then run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_installer.ps1
```

Output:

```text
installer/output/ValorantTrackerSetup.exe
```

Optional WebView2 bootstrapper path:

```text
installer/dependencies/MicrosoftEdgeWebView2Setup.exe
```

## V1 Validation

Run the automated local validation:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate_v1.ps1
```

After building the executable and installer:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate_v1.ps1 -RequireBuildArtifacts
```

Manual beta checklist:

```text
beta_validation_checklist.md
```
