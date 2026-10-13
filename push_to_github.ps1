<#
.SYNOPSIS
    Push HelmetGuard AI ke GitHub.

.DESCRIPTION
    Menjalankan git remote/push. Saat Git Credential Manager meminta
    login, akan terbuka jendela browser - cukup login sekali.

.EXAMPLE
    .\push_to_github.ps1
    .\push_to_github.ps1 -Username wildan-pro
#>
param(
    [string]$Username = "",
    [string]$RepoName = "HelmetGuard-AI",
    [switch]$SkipRemote
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host ""
Write-Host "=== HelmetGuard AI - Push ke GitHub ===" -ForegroundColor Cyan
Write-Host ""

# --- Cek kondisi repo -----------------------------------------------------
$hasCommits = git rev-parse --verify HEAD 2>$dev/null
if (-not $hasCommits) {
    Write-Host "[!] Belum ada commit. Jalankan dulu:" -ForegroundColor Yellow
    Write-Host "    git add -A ; git commit -m `"init`"" -ForegroundColor Gray
    exit 1
}

$untracked = git status --porcelain
if ($untracked) {
    Write-Host "[i] Ada perubahan belum di-commit:" -ForegroundColor Yellow
    Write-Host "    Menyorot: $((($untracked | Measure-Object).Count)) file"
    $answer = Read-Host "    Lanjutkan push tanpa commit? (y/n)"
    if ($answer -ne "y") { Write-Host "[!] Dibatalkan." -ForegroundColor Red; exit 1 }
}

# --- Tentukan username ----------------------------------------------------
if (-not $Username) {
    # Coba tebak dari config git atau remote yang sudah ada
    $existing = git remote get-url origin 2>$dev/null
    if ($existing -match 'github\.com[:/]([^/]+)/') {
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
if (-not $SkipRemote) {
    if (git remote get-url origin 2>$dev/null) {
        Write-Host "[i] Remote 'origin' sudah ada -> $url" -ForegroundColor DarkGray
        git remote set-url origin $url
    } else {
        git remote add origin $url
        Write-Host "[OK] Remote ditambahkan: $url" -ForegroundColor Green
    }
}

git branch -M main 2>$dev/null

# --- Ringkasan sebelum push ----------------------------------------------
$files = git ls-files
$size = 0
foreach ($f in $files) { if (Test-Path $f) { $size += (Get-Item $f).Length } }

Write-Host ""
Write-Host "--- Yang akan di-push ---" -ForegroundColor Cyan
Write-Host "  Repo    : $RepoName"
Write-Host "  File    : $($files.Count)"
Write-Host ("  Ukuran  : {0:N2} MB" -f ($size / 1MB))
Write-Host "  Branch  : main"
Write-Host ""

# --- Push -----------------------------------------------------------------
Write-Host "Menyambung ke GitHub..." -ForegroundColor Cyan
Write-Host "(bila muncul jendela browser, LOGIN dengan akun GitHub kamu)" -ForegroundColor Yellow
Write-Host ""

git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[OK] Push berhasil!" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Buka: https://github.com/$Username/$RepoName" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Langkah berikutnya untuk LinkedIn:" -ForegroundColor White
    Write-Host "  1. Salin URL di atas"
    Write-Host "  2. Buka draft di docs\LINKEDIN_DRAFT.md"
    Write-Host "  3. Paste link repo ke bagian 'Repo:'"
} else {
    Write-Host ""
    Write-Host "[ERROR] Push gagal (kode $LASTEXITCODE)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Kemungkinan penyebab:" -ForegroundColor Yellow
    Write-Host "  - Repo '$RepoName' belum dibuat di github.com/new" -ForegroundColor Gray
    Write-Host "  - Login ditolak / tidak diotorisasi" -ForegroundColor Gray
    Write-Host "  - Password GitHub tidak dipakai (harus token/browser auth)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Coba lagi setelah membuat repo di https://github.com/new" -ForegroundColor Cyan
}

exit $LASTEXITCODE