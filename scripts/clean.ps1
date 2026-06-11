$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

$Targets = @(
    "build",
    "__pycache__",
    "src\__pycache__",
    "src\wbsync\__pycache__",
    "tools\__pycache__",
    "WBSync.spec"
)

foreach ($Target in $Targets) {
    $Path = Join-Path $ProjectRoot $Target
    if (Test-Path $Path) {
        Remove-Item -LiteralPath $Path -Recurse -Force
        Write-Host "Removed $Target"
    }
}

Write-Host "Clean complete."
