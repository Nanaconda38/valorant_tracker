# Valorant Local Tracker

![Windows](https://img.shields.io/badge/platform-Windows-0078D4?style=for-the-badge&logo=windows)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-local_backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Status](https://img.shields.io/badge/status-private_beta-ff4655?style=for-the-badge)

A local-first Windows desktop tracker for VALORANT players.

Valorant Local Tracker detects the local Riot client, follows live game state, enriches player data through HenrikDev, calculates performance scores, and stores match history on the user's machine. It is designed as a lightweight desktop app that can be shared as a single Windows installer.

> This project is not endorsed by Riot Games and is not affiliated with Riot Games, VALORANT, or Tracker Network.

## Highlights

- Native Windows desktop window powered by `pywebview` and Microsoft Edge WebView2.
- Local FastAPI backend running on `127.0.0.1`.
- Riot local client detection through the local lockfile.
- Live lobby, pregame, in-game, and post-match tracking.
- Ally and enemy player cards with ranks, stats, agents, premade hints, and tracker score.
- Local career history backed by SQLite.
- HenrikDev API onboarding with local key storage.
- User data stored under `%APPDATA%\ValorantTracker`.
- Windows installer built with PyInstaller and Inno Setup.
- Optional startup modes:
  - launch with Windows;
  - wait for VALORANT, then launch the tracker.

## Current Status

The app is in private beta. It is ready for controlled testing with friends, but not yet intended as a polished public release.

Recommended beta checks are documented in [`docs/beta_validation_checklist.md`](docs/beta_validation_checklist.md).

## Tech Stack

| Layer | Technology |
| --- | --- |
| Desktop shell | `pywebview` |
| Local backend | FastAPI, Uvicorn |
| Frontend | HTML, CSS, vanilla JavaScript |
| Storage | SQLite |
| Packaging | PyInstaller |
| Installer | Inno Setup 6 |
| Runtime data | `%APPDATA%\ValorantTracker` |

## Privacy Model

Valorant Local Tracker is intentionally local-first:

- no central backend;
- no shared user database;
- no cloud sync;
- no telemetry pipeline;
- each installation owns its local settings, logs, cache, and SQLite database.

The HenrikDev API key is not committed to the repository and should never be distributed in `.env` files or build artifacts. Runtime configuration belongs in the user's local app data directory.

## User Installation

The Windows installer output is:

```text
installer/output/ValorantTrackerSetup.exe
```

The installer:

- installs the desktop app per user;
- creates Start Menu shortcuts;
- can create a desktop shortcut;
- creates `%APPDATA%\ValorantTracker`;
- preserves local user data on uninstall;
- includes the Microsoft Edge WebView2 bootstrapper when present at:

```text
installer/dependencies/MicrosoftEdgeWebView2Setup.exe
```

## Run From Source

Create and activate a virtual environment, then install dependencies:

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r .\requirements.txt
```

Run the desktop app:

```powershell
.\venv\Scripts\python.exe .\desktop_main.py
```

Run the browser/dev mode:

```powershell
.\venv\Scripts\python.exe .\desktop_main.py --dev
```

Run the Valorant watcher manually:

```powershell
.\venv\Scripts\python.exe .\desktop_main.py --watch-valorant
```

## Build

Build the Windows executable:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_exe.ps1
```

Output:

```text
dist/ValorantTracker/ValorantTracker.exe
```

Build the installer:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_installer.ps1
```

Build both the executable and installer:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_installer.ps1 -BuildExe
```

More details are available in [`docs/build_windows.md`](docs/build_windows.md) and [`installer/README.md`](installer/README.md).

## Validation

Run the local validation script:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate_v1.ps1
```

After building release artifacts:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate_v1.ps1 -RequireBuildArtifacts
```

## Repository Layout

```text
.
|-- app.py                         # FastAPI app and VALORANT tracking logic
|-- desktop_main.py                # Desktop launcher and pywebview lifecycle
|-- database.py                    # SQLite persistence
|-- settings_manager.py            # Local settings
|-- secrets_manager.py             # Local HenrikDev key storage
|-- autostart_manager.py           # Windows startup integration
|-- templates/                     # App HTML
|-- static/                        # CSS, JS, and game assets
|-- scripts/                       # Build and validation scripts
|-- tools/                         # Calibration, capture, and asset utility scripts
|-- docs/                          # Specifications, plans, and beta checklist
|-- installer/                     # Inno Setup packaging
|-- valorant_tracker.spec          # PyInstaller spec
`-- README.md                      # GitHub project page
```

## Roadmap

- Harden beta installer testing on clean Windows machines.
- Improve first-launch onboarding and failure messages.
- Add release screenshots and a short demo GIF.
- Add automated UI smoke checks for the desktop shell.
- Prepare a signed installer for wider distribution.

## Legal Notice

VALORANT and Riot Games are trademarks or registered trademarks of Riot Games, Inc. This project is independent and community-made.
