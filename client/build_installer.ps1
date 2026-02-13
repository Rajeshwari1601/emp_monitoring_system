# Build script for Employee Monitoring System Client

$ErrorActionPreference = "Stop"

Write-Host "--- Starting Build Process ---" -ForegroundColor Cyan

# 1. Clean previous builds
if (Test-Path "dist") {
    Write-Host "Cleaning dist folder..."
    Remove-Item -Path "dist" -Recurse -Force
}
if (Test-Path "build") {
    Write-Host "Cleaning build folder..."
    Remove-Item -Path "build" -Recurse -Force
}

# 2. Build Python Executable using PyInstaller
Write-Host "Building Python Executable using venv..." -ForegroundColor Yellow
$pyinstaller_path = ".\venv\Scripts\pyinstaller.exe"
if (-not (Test-Path $pyinstaller_path)) {
    Write-Error "PyInstaller not found in venv\Scripts. Please run: .\venv\Scripts\pip.exe install pyinstaller"
    exit 1
}
& $pyinstaller_path EmployeeMonitoring.spec

if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller build failed!"
    exit $LASTEXITCODE
}

# 3. Build MSI Installer using WiX v4+ (wix.exe)
Write-Host "Building MSI Installer..." -ForegroundColor Yellow
cd installer

# Check if wix is available
try {
    & wix --version
} catch {
    Write-Error "WiX Toolset (wix.exe) not found in PATH. Please install it with: dotnet tool install --global wix"
    exit 1
}

# Compile and Link (WiX v4/v5/v6 single step)
# We add the UI extension so the installer has a wizard
# We add the Util extension for ShellExec (Launch on Finish)
& wix build Product.wxs -ext WixToolset.UI.wixext -ext WixToolset.Util.wixext -o ..\dist\EmployeeMonitoring.msi

if ($LASTEXITCODE -ne 0) {
    Write-Error "WiX build failed!"
    exit $LASTEXITCODE
}

cd ..

Write-Host "--- Build Successful! ---" -ForegroundColor Green
Write-Host "Installer created at: dist\EmployeeMonitoring.msi"
