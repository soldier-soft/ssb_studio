# ==============================================================================
#  SSB Practice Studio - Automated Windows Web Installer
#  Run via: irm https://soldier-soft.github.io/ssb_studio/install.ps1 | iex
# ==============================================================================
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ErrorActionPreference = "Stop"

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "   SSB PRACTICE STUDIO - 1-CLICK WEB INSTALLER (WINDOWS 10/11)  " -ForegroundColor White
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

$installDir = Join-Path $env:LOCALAPPDATA "SSBPracticeStudioApp"
$zipPath = Join-Path $env:TEMP "SSB_Practice_Studio_Windows.zip"
$repoZipUrl = "https://github.com/soldier-soft/ssb_studio/releases/latest/download/SSB_Practice_Studio_Windows.zip"

Write-Host "[1/4] Downloading latest release from GitHub..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri $repoZipUrl -OutFile $zipPath -UseBasicParsing
} catch {
    Write-Host "[INFO] Checking GitHub repository download..." -ForegroundColor Yellow
    $repoZipUrl = "https://github.com/soldier-soft/ssb_studio/releases/download/v1.0.0/SSB_Practice_Studio_Windows.zip"
    Invoke-WebRequest -Uri $repoZipUrl -OutFile $zipPath -UseBasicParsing
}

Write-Host "[2/4] Extracting package to $installDir..." -ForegroundColor Yellow
if (Test-Path $installDir) {
    Remove-Item -Recurse -Force $installDir -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Force -Path $installDir | Out-Null
Expand-Archive -Path $zipPath -DestinationPath $installDir -Force
Remove-Item -Force $zipPath -ErrorAction SilentlyContinue

Write-Host "[3/4] Creating Windows Desktop Shortcut..." -ForegroundColor Yellow
$exePath = Join-Path $installDir "SSBPracticeStudio\SSBPracticeStudio.exe"
if (-not (Test-Path $exePath)) {
    $exePath = Join-Path $installDir "SSBPracticeStudio.exe"
}
$iconPath = Join-Path $installDir "SSBPracticeStudio\_internal\assets\app_icon.ico"
if (-not (Test-Path $iconPath)) { $iconPath = $exePath }

$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)
$ShortcutPath = Join-Path $DesktopPath "SSB Practice Studio.lnk"
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $exePath
$Shortcut.WorkingDirectory = (Split-Path -Parent $exePath)
$Shortcut.IconLocation = "$iconPath,0"
$Shortcut.Description = "SSB Practice Studio - Officer Assessment Psychological Tests (WAT, SRT, TAT)"
$Shortcut.Save()

Write-Host "   --> Desktop shortcut created at: $ShortcutPath" -ForegroundColor Green

Write-Host "[4/4] Launching SSB Practice Studio..." -ForegroundColor Yellow
Start-Process -FilePath $exePath
Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "   INSTALLATION COMPLETE! SSB Practice Studio is now running.   " -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
