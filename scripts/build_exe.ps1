param(
    [switch]$NoClean
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Python = Join-Path $Root "venv\Scripts\python.exe"
$Spec = Join-Path $Root "valorant_tracker.spec"
$DistDir = Join-Path $Root "dist"
$BuildDir = Join-Path $Root "build"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Python venv not found at $Python"
}

if (-not (Test-Path -LiteralPath $Spec)) {
    throw "PyInstaller spec not found at $Spec"
}

Push-Location $Root
try {
    & $Python -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('PyInstaller') else 1)"
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller is not installed. Run: .\venv\Scripts\python.exe -m pip install -r .\requirements.txt"
    }

    if (-not $NoClean) {
        Remove-Item -LiteralPath (Join-Path $DistDir "ValorantTracker") -Recurse -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath (Join-Path $BuildDir "valorant_tracker") -Recurse -Force -ErrorAction SilentlyContinue
    }

    $env:VALORANT_TRACKER_SKIP_DOTENV = "1"
    & $Python -m PyInstaller --noconfirm --clean $Spec
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller build failed."
    }

    $OutputExe = Join-Path $DistDir "ValorantTracker\ValorantTracker.exe"
    if (-not (Test-Path -LiteralPath $OutputExe)) {
        throw "Build completed but executable was not found at $OutputExe"
    }

    $Forbidden = @(".env", "tracker.db", "server.log", "server.err.log", "lcu_debug_output.json")
    foreach ($Name in $Forbidden) {
        $Found = Get-ChildItem -LiteralPath (Join-Path $DistDir "ValorantTracker") -Recurse -Force -Filter $Name -ErrorAction SilentlyContinue
        if ($Found) {
            throw "Forbidden file included in build output: $($Found[0].FullName)"
        }
    }

    Write-Host "Build complete: $OutputExe"
}
finally {
    Pop-Location
}
