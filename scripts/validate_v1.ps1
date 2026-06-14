param(
    [switch]$RequireBuildArtifacts
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Python = Join-Path $Root "venv\Scripts\python.exe"
$TempData = Join-Path $Root "tmp\validation-v1"
$DistExe = Join-Path $Root "dist\ValorantTracker\ValorantTracker.exe"
$SetupExe = Join-Path $Root "installer\output\ValorantTrackerSetup.exe"

$Results = New-Object System.Collections.Generic.List[object]

function Add-Result {
    param(
        [string]$Name,
        [bool]$Passed,
        [string]$Details = ""
    )
    $Results.Add([pscustomobject]@{
        Check = $Name
        Passed = $Passed
        Details = $Details
    })
}

function Invoke-Check {
    param(
        [string]$Name,
        [scriptblock]$Script
    )
    try {
        $Details = & $Script
        Add-Result $Name $true ($Details -join "`n")
    }
    catch {
        Add-Result $Name $false $_.Exception.Message
    }
}

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Python venv not found at $Python"
}

Push-Location $Root
try {
    if (Test-Path -LiteralPath $TempData) {
        Remove-Item -LiteralPath $TempData -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $TempData | Out-Null
    $env:VALORANT_TRACKER_DATA_DIR = $TempData
    $env:VALORANT_TRACKER_SKIP_DOTENV = "1"
    $env:HENRIK_API_KEY = ""

    Invoke-Check "Python compile" {
        & $Python -m py_compile `
            .\app.py `
            .\desktop_main.py `
            .\app_logging.py `
            .\app_paths.py `
            .\settings_manager.py `
            .\secrets_manager.py `
            .\autostart_manager.py `
            .\api_client.py `
            .\database.py `
            .\lockfile_scanner.py
        if ($LASTEXITCODE -ne 0) { throw "py_compile failed" }
        "ok"
    }

    Invoke-Check "Runtime paths stay outside repo" {
        $Output = & $Python -c "from app_paths import database_path, settings_path, logs_dir, cache_dir; print(database_path()); print(settings_path()); print(logs_dir()); print(cache_dir())"
        foreach ($Line in $Output) {
            if (-not $Line.StartsWith($TempData)) {
                throw "Runtime path outside validation data dir: $Line"
            }
        }
        $Output
    }

    Invoke-Check "Settings and DB initialize" {
        $Output = & $Python -c "from settings_manager import SettingsManager; from database import DatabaseManager; from app_paths import settings_path, database_path; s=SettingsManager().load(); DatabaseManager().init_db(); print(settings_path().exists()); print(database_path().exists()); print(s['app']['first_launch_completed'])"
        if ($Output[0] -ne "True" -or $Output[1] -ne "True") {
            throw "settings/db files were not created"
        }
        $Output
    }

    Invoke-Check "FastAPI config routes present" {
        $Output = & $Python -c "import app; routes=sorted(r.path for r in app.app.routes if hasattr(r, 'methods')); required=['/api/settings','/api/config/status','/api/config/henrik-key','/api/config/henrik-key/verify','/api/settings/open-data-folder','/api/settings/open-logs-folder','/api/settings/reload-cache']; missing=[r for r in required if r not in routes]; print('missing=' + ','.join(missing)); raise SystemExit(1 if missing else 0)"
        if ($LASTEXITCODE -ne 0) { throw ($Output -join "`n") }
        $Output
    }

    Invoke-Check "Secret redaction" {
        $RedactionScript = @'
from app_logging import redact_text

s = redact_text("Authorization: Bearer abc.def.ghi accessToken='secret' password='pw' api_key='k'")
print(s)
raise SystemExit(1 if "secret" in s or "abc.def.ghi" in s or "'pw'" in s else 0)
'@
        $Output = $RedactionScript | & $Python -
        if ($LASTEXITCODE -ne 0) { throw "redaction failed: $Output" }
        $Output
    }

    Invoke-Check "Autostart command dry-run" {
        $Output = & $Python -c "from autostart_manager import app_command, watcher_command, startup_status; print(app_command()); print(watcher_command()); print(startup_status()['supported'])"
        if ($Output[1] -notmatch "--watch-valorant") {
            throw "watcher command missing --watch-valorant"
        }
        $Output
    }

    Invoke-Check "Desktop backend smoke" {
        $SmokeScript = @'
import requests
from desktop_main import BackendServer, find_free_port

server = BackendServer("127.0.0.1", find_free_port())
server.start()
try:
    response = requests.get(f"{server.url}/api/settings", timeout=3)
    print(server.url)
    print(response.status_code)
    print(response.json()["app"]["version"])
    raise SystemExit(0 if response.status_code == 200 else 1)
finally:
    server.stop()
'@
        $Output = $SmokeScript | & $Python -
        if ($LASTEXITCODE -ne 0) { throw "desktop backend smoke failed" }
        $Output
    }

    Invoke-Check "Build artifacts" {
        $Messages = @()
        if (Test-Path -LiteralPath $DistExe) {
            $Messages += "exe=$DistExe"
        }
        elseif ($RequireBuildArtifacts) {
            throw "Missing $DistExe"
        }
        else {
            $Messages += "exe missing (ok before build)"
        }

        if (Test-Path -LiteralPath $SetupExe) {
            $Messages += "setup=$SetupExe"
        }
        elseif ($RequireBuildArtifacts) {
            throw "Missing $SetupExe"
        }
        else {
            $Messages += "setup missing (ok before installer build)"
        }
        $Messages
    }

    Invoke-Check "No forbidden files in dist" {
        $DistRoot = Join-Path $Root "dist\ValorantTracker"
        if (-not (Test-Path -LiteralPath $DistRoot)) {
            return "dist missing (ok before build)"
        }
        $Forbidden = @(".env", "tracker.db", "server.log", "server.err.log", "lcu_debug_output.json")
        foreach ($Name in $Forbidden) {
            $Found = Get-ChildItem -LiteralPath $DistRoot -Recurse -Force -Filter $Name -ErrorAction SilentlyContinue
            if ($Found) {
                throw "Forbidden file found: $($Found[0].FullName)"
            }
        }
        "ok"
    }
}
finally {
    Pop-Location
}

$Results | Format-Table -AutoSize

$Failed = $Results | Where-Object { -not $_.Passed }
if ($Failed) {
    exit 1
}

exit 0
