param(
    [string]$InnoSetupCompiler = "",
    [switch]$BuildExe
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$SpecOutputExe = Join-Path $Root "dist\ValorantTracker\ValorantTracker.exe"
$InstallerScript = Join-Path $Root "installer\ValorantTracker.iss"
$BuildExeScript = Join-Path $Root "scripts\build_exe.ps1"

function Find-Iscc {
    param([string]$ExplicitPath)

    if ($ExplicitPath) {
        if (-not (Test-Path -LiteralPath $ExplicitPath)) {
            throw "Inno Setup compiler not found at $ExplicitPath"
        }
        return (Resolve-Path -LiteralPath $ExplicitPath).Path
    }

    $Command = Get-Command iscc.exe -ErrorAction SilentlyContinue
    if ($Command) {
        return $Command.Source
    }

    $Candidates = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe",
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe")
    )
    foreach ($Candidate in $Candidates) {
        if (Test-Path -LiteralPath $Candidate) {
            return $Candidate
        }
    }

    throw "Inno Setup compiler not found. Install Inno Setup 6 or pass -InnoSetupCompiler path\to\ISCC.exe"
}

Push-Location $Root
try {
    if ($BuildExe) {
        powershell -NoProfile -ExecutionPolicy Bypass -File $BuildExeScript
    }

    if (-not (Test-Path -LiteralPath $SpecOutputExe)) {
        throw "Missing $SpecOutputExe. Build the executable first with: powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_exe.ps1"
    }

    if (-not (Test-Path -LiteralPath $InstallerScript)) {
        throw "Installer script not found at $InstallerScript"
    }

    $Iscc = Find-Iscc $InnoSetupCompiler
    & $Iscc $InstallerScript
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup build failed."
    }

    $SetupExe = Join-Path $Root "installer\output\ValorantTrackerSetup.exe"
    if (-not (Test-Path -LiteralPath $SetupExe)) {
        throw "Installer build completed but setup exe was not found at $SetupExe"
    }

    Write-Host "Installer complete: $SetupExe"
}
finally {
    Pop-Location
}
