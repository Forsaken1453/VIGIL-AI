<#
.SYNOPSIS
    Buat shortcut HelmetGuard AI di Desktop + Start Menu.

.DESCRIPTION
    Installer 4.5 GB itu berlebihan untuk project ini. Yang kamu butuhkan
    cuma "double-click dan jalan", dan itu sudah bisa-delayah lewat shortcut.

.EXAMPLE
    .\create_shortcut.ps1
#>
$ErrorActionPreference = "Stop"

$Exe    = Join-Path $PSScriptRoot "dist\HelmetGuard\HelmetGuard.exe"
$Folder = Split-Path $Exe -Parent
$Icon   = Join-Path $PSScriptRoot "docs\helmetguard.ico"

if (-not (Test-Path $Exe)) {
    Write-Host "[!] EXE tidak ditemukan: $Exe" -ForegroundColor Red
    Write-Host "    Jalankan dulu: .venv\Scripts\python scripts\build_exe.py" -ForegroundColor Yellow
    exit 1
}

# --- Shortcut COM object ---
$shell = New-Object -ComObject WScript.Shell

function New-Shortcut([string]$path, [string]$target, [string]$workdir) {
    $sc = $shell.CreateShortcut($path)
    $sc.TargetPath       = $target
    $sc.WorkingDirectory = $workdir
    $sc.Description      = "Real-Time Construction PPE Detection (YOLO11)"
    if (Test-Path $Icon) { $sc.IconLocation = "$Icon,0" }
    $sc.Save()
    Write-Host "[OK] $path" -ForegroundColor Green
}

$desktop = [Environment]::GetFolderPath("Desktop")
$startMenu = Join-Path ([Environment]::GetFolderPath("Programs")) "HelmetGuard AI"

# --- Buat Start Menu folder ---
if (-not (Test-Path $startMenu)) {
    New-Item -ItemType Directory -Path $startMenu -Force | Out-Null
}

# --- Shortcut di Desktop & Start Menu ---
New-Shortcut (Join-Path $desktop "HelmetGuard AI.lnk")  $Exe $Folder
New-Shortcut (Join-Path $startMenu "HelmetGuard AI.lnk") $Exe $Folder

Write-Host ""
Write-Host "Selesai." -ForegroundColor Cyan
Write-Host "  Desktop   : $desktop\HelmetGuard AI.lnk" -ForegroundColor Gray
Write-Host "  Start Menu: Start Menu\HelmetGuard AI\HelmetGuard AI.lnk" -ForegroundColor Gray
Write-Host ""
Write-Host "Catatan: shortcut ini menunjuk ke folder di drive D:." -ForegroundColor Yellow
Write-Host "Kalau folder dipindah, shortcut harus dibuat ulang." -ForegroundColor Yellow