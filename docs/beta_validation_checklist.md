# Valorant Tracker V1 Beta Validation Checklist

Use this checklist before sharing a build with friends.

## 1. Local Automated Validation

Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate_v1.ps1
```

After building the executable and installer, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate_v1.ps1 -RequireBuildArtifacts
```

## 2. Build Validation

- [ ] `.\scripts\build_exe.ps1` creates `dist\ValorantTracker\ValorantTracker.exe`.
- [ ] `.\scripts\build_installer.ps1` creates `installer\output\ValorantTrackerSetup.exe`.
- [ ] Build output does not contain:
  - `.env`
  - `tracker.db`
  - `server.log`
  - `server.err.log`
  - `lcu_debug_output.json`
  - `data\live_api_snapshots`
  - screenshot folders
- [ ] App data is created under `%APPDATA%\ValorantTracker`.
- [ ] Logs are created under `%APPDATA%\ValorantTracker\logs`.

## 3. Fresh Machine Install

- [ ] Run `ValorantTrackerSetup.exe`.
- [ ] App installs into `%LOCALAPPDATA%\Programs\ValorantTracker`.
- [ ] Start Menu shortcut launches the app.
- [ ] Optional desktop shortcut launches the app.
- [ ] No console window appears during normal use.
- [ ] If WebView2 is missing, installer handles it or displays a clear warning.

## 4. Onboarding

- [ ] First launch without a HenrikDev key shows `Configuration HenrikDev API`.
- [ ] `Open HenrikDev` opens the HenrikDev dashboard.
- [ ] Empty key shows a clear warning.
- [ ] Invalid key shows a clear error.
- [ ] Valid key is saved.
- [ ] After saving a valid key, onboarding no longer appears.
- [ ] `Continue Without Key` hides onboarding and the app remains usable with limited live scouting stats.

## 5. Settings

- [ ] Settings modal opens from the header.
- [ ] API status shows `Configured` when a key exists.
- [ ] `Verify Only` checks a pasted key without saving it.
- [ ] `Verify and Save` replaces the saved key.
- [ ] `Delete Key` removes the local key.
- [ ] `Open Data Folder` opens `%APPDATA%\ValorantTracker`.
- [ ] `Open Logs` opens `%APPDATA%\ValorantTracker\logs`.
- [ ] `Reload Cache` completes without breaking the dashboard.
- [ ] `Launch on Windows startup` creates/removes the `ValorantTracker` Run entry.
- [ ] `Launch when Valorant starts` creates/removes the `ValorantTrackerValorantWatcher` Run entry.

## 6. Runtime With Valorant Closed

- [ ] App opens normally.
- [ ] Status displays offline/searching state.
- [ ] Dashboard does not crash.
- [ ] Career section loads from local DB.

## 7. Runtime With Valorant Open

- [ ] App detects the local Riot client.
- [ ] App displays the current account name.
- [ ] Menu/lobby state is stable.
- [ ] Pregame loads allies.
- [ ] Core-game loads allies and enemies.
- [ ] HenrikDev rate-limit or API failure shows fallback stats instead of crashing.

## 8. Post-Match Persistence

- [ ] Completed match is detected.
- [ ] Match details are cached locally.
- [ ] Match is inserted into `%APPDATA%\ValorantTracker\tracker.db`.
- [ ] RR session widget updates.
- [ ] Career history shows the new match.
- [ ] Match detail modal opens from career history.

## 9. Uninstall

- [ ] Uninstall removes installed app files.
- [ ] Uninstall removes app startup entries.
- [ ] `%APPDATA%\ValorantTracker\tracker.db` is preserved.
- [ ] `%APPDATA%\ValorantTracker\logs` is preserved.
- [ ] Reinstall keeps the local career DB.

## 10. Beta Feedback To Collect

Ask each tester for:

- Windows version.
- Whether WebView2 warning/install appeared.
- Whether SmartScreen blocked launch.
- Whether onboarding was clear.
- Whether Valorant detection worked.
- Whether live lobby stats appeared.
- Whether post-match save worked.
- `%APPDATA%\ValorantTracker\logs\valorant_tracker.log` if something failed.
