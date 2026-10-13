# Akses environment HelmetGuard AI
# Jalankan di PowerShell:  .\activate_env.ps1
# Jangan di-source dari Git (sensitive path tidak, tapi tetap bukan best practice).

$ProjectRoot = 'D:\Project\HelmetGuard-AI'
$VenvPython  = "$ProjectRoot\.venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Venv tidak ditemukan di $VenvPython" -ForegroundColor Red
    Write-Host "Buat dulu:  D:\Python312\python.exe -m venv `"$ProjectRoot\.venv`"" -ForegroundColor Yellow
    return
}

# Pastikan cache/temp tidak menyentuh drive C:
$env:PIP_CACHE_DIR  = 'D:\Temp\pip-cache'
$env:TEMP           = 'D:\Temp'
$env:TMP            = 'D:\Temp'
$env:TORCH_HOME     = 'D:\Temp\torch'
$env:HF_HOME        = 'D:\Temp\huggingface'
$env:YOLO_CONFIG_DIR = 'D:\Temp\yolo'

Set-Location $ProjectRoot

# Alias supaya mudah
function hg { & $VenvPython @args }
function hgcli { & $VenvPython "$ProjectRoot\scripts\run_cli.py" @args }

Write-Host "HelmetGuard AI aktif" -ForegroundColor Green
Write-Host "  python : $VenvPython"
Write-Host "  folder : $ProjectRoot"
Write-Host "  contoh : hg main.py"
Write-Host "           hg scripts\train.py --help"