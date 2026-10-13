<#
.SYNOPSIS
    Push VIGIL ke GitHub.

.DESCRIPTION
    Menjalankan git remote/push. Saat Git Credential Manager meminta
    login, akan terbuka jendela browser - cukup login sekali.

.EXAMPLE
    .\push_to_github.ps1 -Username Forsaken1453
#>
param(
    [string]$Username = "",
    [string]$RepoName = "VIGIL-AI"
)

# CATATAN PENTING: JANGAN set ErrorActionPreference="Stop" di file ini.
# Git menulis pesan "error" ke stderr, dan di PowerShell stderr + "Stop"
# menjadi terminating error - padahal "remote origin belum ada" itu kondisi
# NORMAL, bukan kegagalan. Kita set "Continue" dan tangani exit code manual.
$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

function Invoke-Git {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$GitArgs)
    $out = & git @GitArgs 2>&1
    return [pscustomobject]@{ Output = $out; Code = $LASTEXITCODE }
}

Write-Host ""
Write-Host "=== VIGIL - Push ke GitHub ===" -ForegroundColor Cyan
Write-Host ""

# --- Cek kondisi repo -----------------------------------------------------
if ((Invoke-Git rev-parse --verify HEAD).Code -ne 0) {
    Write-Host "[!] Belum ada commit. Jalankan dulu:" -ForegroundColor Yellow
    Write-Host "    git add -A ; git commit -m `"init`"" -ForegroundColor Gray
    exit 1
}

# --- Perubahan belum di-commit -------------------------------------------
$untracked = git status --porcelain
if ($untracked) {
    Write-Host "[i] Ada perubahan belum di-commit:" -ForegroundColor Yellow
    Write-Host "    ($((($untracked | Measure-Object).Count)) file)"
    $answer = Read-Host "    Lanjutkan push tanpa commit? (y/n)"
    if ($answer -ne "y") {
        Write-Host "[!] Dibatalkan." -ForegroundColor Red
        exit 1
    }
}

# --- Tentukan username ----------------------------------------------------
if (-not $Username) {
    $existing = (Invoke-Git remote get-url origin)
    if ($existing.Code -eq 0 -and "$($existing.Output)" -match 'github\.com[:/]([^/]+)/') {
        $Username = $Matches[1]
        Write-Host "[i] Username dari remote lama: $Username" -ForegroundColor DarkGray
    }
}

if (-not $Username) {
    Write-Host "[!] Username GitHub tidak diketahui." -ForegroundColor Red
    Write-Host "    Jalankan ulang dengan: .\push_to_github.ps1 -Username NAMA_KAMU" -ForegroundColor Yellow
    exit 1
}

$url = "https://github.com/$Username/$RepoName.git"

# --- Remote ---------------------------------------------------------------
$remoteList = @(git remote)
if ($remoteList -contains "origin") {
    Write-Host "[i] Remote 'origin' sudah ada -> diperbarui" -ForegroundColor DarkGray
    Invoke-Git remote set-url origin $url | Out-Null
} else {
    Invoke-Git remote add origin $url | Out-Null
    Write-Host "[OK] Remote ditambahkan: $url" -ForegroundColor Green
}

Invoke-Git branch -M main | Out-Null

# --- Ringkasan sebelum push ----------------------------------------------
$files = @(git ls-files)
$size = 0
foreach ($f in $files) {
    if (Test-Path $f) { $size += (Get-Item $f).Length }
}

Write-Host ""
Write-Host "--- Yang akan di-push ---" -ForegroundColor Cyan
Write-Host "  Repo   : $Username/$RepoName"
Write-Host "  File   : $($files.Count)"
Write-Host ("  Ukuran : {0:N2} MB" -f ($size / 1MB))
Write-Host "  Branch : main"
Write-Host ""

# --- Push -----------------------------------------------------------------
Write-Host "Menyambung ke GitHub..." -ForegroundColor Cyan
Write-Host "(bila muncul jendela browser, LOGIN dengan akun GitHub kamu)" -ForegroundColor Yellow
Write-Host ""

$push = Invoke-Git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[OK] Push berhasil!" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Buka: https://github.com/$Username/$RepoName" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Langkah berikutnya untuk LinkedIn:" -ForegroundColor White
    Write-Host "  1. Salin URL di atas"
    Write-Host "  2. Buka draft di docs\LINKEDIN_DRAFT.md"
    Write-Host '  3. Paste link repo ke bagian "Repo:"'
} else {
    Write-Host ""
    Write-Host "[ERROR] Push gagal" -ForegroundColor Red
    Write-Host ""
    Write-Host "Pesan git:" -ForegroundColor Yellow
    $push.Output | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkYellow }
    Write-Host ""
    Write-Host "Kemungkinan penyebab:" -ForegroundColor Yellow
    Write-Host "  - Repo '$RepoName' belum dibuat di https://github.com/new" -ForegroundColor Gray
    Write-Host "  - Login ditolak / tidak diotorisasi" -ForegroundColor Gray
    Write-Host "  - GitHub menolak password biasa (butuh login browser/token)" -ForegroundColor Gray
}

exit $LASTEXITCODE