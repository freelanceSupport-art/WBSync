$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$Python = (Get-Command python -ErrorAction Stop).Source

Write-Host "Using Python: $Python"
& $Python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing PyInstaller..."
    & $Python -m pip install pyinstaller
}

& $Python -c "import PIL" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing Pillow..."
    & $Python -m pip install pillow
}

$IconSource = Join-Path $ProjectRoot "assets\brand\Icon.png"
if (-not (Test-Path $IconSource)) {
    throw "assets\brand\Icon.png was not found."
}

& $Python ".\tools\make_icon.py"
if (-not (Test-Path (Join-Path $ProjectRoot "assets\generated\icon.ico"))) {
    throw "icon.ico generation failed."
}

$ExePath = Join-Path $ProjectRoot "dist\WBSync.exe"
if (Test-Path $ExePath) {
    try {
        Remove-Item -LiteralPath $ExePath -Force
    }
    catch {
        throw "Could not remove existing WBSync.exe. Close the app and run this script again."
    }
}

if (Test-Path (Join-Path $ProjectRoot "build")) {
    Remove-Item -LiteralPath (Join-Path $ProjectRoot "build") -Recurse -Force
}
if (Test-Path (Join-Path $ProjectRoot "WBSync.spec")) {
    Remove-Item -LiteralPath (Join-Path $ProjectRoot "WBSync.spec") -Force
}

& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name WBSync `
    --icon ".\assets\generated\icon.ico" `
    --add-data "assets;assets" `
    wbsync.py

if (-not (Test-Path $ExePath)) {
    throw "EXE build failed: $ExePath"
}

if (Test-Path (Join-Path $ProjectRoot "build")) {
    Remove-Item -LiteralPath (Join-Path $ProjectRoot "build") -Recurse -Force
}
if (Test-Path (Join-Path $ProjectRoot "WBSync.spec")) {
    Remove-Item -LiteralPath (Join-Path $ProjectRoot "WBSync.spec") -Force
}

Write-Host ""
Write-Host "Build complete:"
Write-Host $ExePath
