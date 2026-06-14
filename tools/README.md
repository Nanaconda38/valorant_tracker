# Tools

Utility scripts used during development, calibration, asset sync, screenshots, and OCR extraction.

These scripts are not part of the normal desktop runtime and are excluded from the packaged Windows app.

Run them from the repository root so their relative paths still resolve correctly:

```powershell
.\venv\Scripts\python.exe .\tools\calibration_store.py summary
.\venv\Scripts\python.exe .\tools\extract_tracker_scoreboards.py
.\venv\Scripts\python.exe .\tools\calibrate_tracker_score.py
```
