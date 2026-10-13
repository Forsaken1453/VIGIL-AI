# Screenshot jendela VIGIL -> docs/gui_screenshot.png
# DPI-AWARE: tanpa ini, GetWindowRect mengembalikan koordinat virtual (logical)
# sementara hasil screenshot berformat physical, sehingga crop meleset.

Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win {
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
    [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr h);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
}
"@ -ErrorAction SilentlyContinue

#WAJIB dipanggil SEBELUM GetWindowRect agar koordinat = piksel fisik
[void][Win]::SetProcessDPIAware()

$ErrorActionPreference = "Continue"
$ProjectDir = 'D:\Project\VIGIL'
$Output = Join-Path $ProjectDir 'docs\gui_screenshot.jpg'

# GetWindowRect mengikutsertakan invisible resize border (~8-14px), jadi
# tanpa inset ini tepi screenshot menyisakan sedikit jendela di belakang.
$Inset = 16

# --- Bersihkan proses lama ---
Get-Process python, VIGIL -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# --- Buat skrip launcher yang auto-start deteksi ---
$Launcher = Join-Path $env:TEMP 'vigil_shot.py'
@'
import sys, threading, time
sys.path.insert(0, r"D:\Project\VIGIL")
from src.gui import VigilApp
app = VigilApp()
def go():
    time.sleep(3)
    app._start_detection()
threading.Thread(target=go, daemon=True).start()
app.mainloop()
'@ | Out-File -FilePath $Launcher -Encoding utf8

# --- Jalankan app dengan console disembunyikan ---
$env:TEMP = 'D:\Temp'; $env:TMP = 'D:\Temp'; $env:YOLO_CONFIG_DIR = 'D:\Temp\yolo'
$Python = Join-Path $ProjectDir '.venv\Scripts\python.exe'
Start-Process -FilePath $Python -ArgumentList $Launcher -WorkingDirectory $ProjectDir -WindowStyle Hidden

Write-Host "Menunggu GUI + deteksi berjalan..." -ForegroundColor Cyan
Start-Sleep -Seconds 32

# --- Cari jendela VIGIL ---
$proc = Get-Process python -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowTitle -like '*VIGIL*' } |
        Select-Object -First 1

if (-not $proc) {
    Write-Host "[ERROR] Jendela VIGIL tidak ditemukan." -ForegroundColor Red
    exit 1
}

[void][Win]::ShowWindow($proc.MainWindowHandle, 9)
[void][Win]::BringWindowToTop($proc.MainWindowHandle)
[void][Win]::SetForegroundWindow($proc.MainWindowHandle)
Start-Sleep -Seconds 4

# --- Ambil rect dalam PIKSEL FISIK ---
$r = New-Object Win+RECT
[void][Win]::GetWindowRect($proc.MainWindowHandle, [ref]$r)
$w = $r.R - $r.L; $h = $r.B - $r.T
Write-Host "Window rect (px fisik): $($r.L),$($r.T)  ${w}x${h}" -ForegroundColor Gray

if ($w -le 0 -or $h -le 0) {
    Write-Host "[ERROR] Rect tidak valid." -ForegroundColor Red
    exit 1
}

# --- Screenshot layar penuh, lalu crop ke window ---
$full = New-Object System.Drawing.Bitmap 1920, 1080
$g = [System.Drawing.Graphics]::FromImage($full)
$g.CopyFromScreen(0, 0, 0, 0, (New-Object System.Drawing.Size(1920, 1080)))
$g.Dispose()

$cropRect = New-Object System.Drawing.Rectangle(
    ($r.L + $Inset), ($r.T + $Inset),
    ($w - 2 * $Inset), ($h - 2 * $Inset)
)
$crop = $full.Clone($cropRect, $full.PixelFormat)
$full.Dispose()

# Simpan sebagai JPG quality 92: PNG untuk UI flat-textury besar (~1.2 MB),
# JPG cuma ~250 KB dengan selisih visual yang nyaris tak terlihat.
$jpg = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() |
       Where-Object { $_.MimeType -eq 'image/jpeg' }
$params = New-Object System.Drawing.Imaging.EncoderParameters(1)
$params.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter(
    [System.Drawing.Imaging.Encoder]::Quality, 92L)
$crop.Save($Output, $jpg, $params)
$crop.Dispose()

$sizeKB = [math]::Round((Get-Item $Output).Length / 1KB, 1)
Write-Host "[OK] $Output (${sizeKB} KB)" -ForegroundColor Green

Remove-Item $Launcher -Force -ErrorAction SilentlyContinue
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue