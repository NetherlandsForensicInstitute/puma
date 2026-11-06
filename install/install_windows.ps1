# Installs everything Puma needs on Windows: Python, adb, Node.js, Appium with its driver, Tesseract and ffmpeg.
# Then it creates a venv in the repository root with the requirements of Puma.
# Run it again at any time: it skips what is already installed.
#
# Usage: powershell -ExecutionPolicy Bypass -File install\install_windows.ps1
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'  # makes Invoke-WebRequest fast in Windows PowerShell
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$PumaRoot = Split-Path $PSScriptRoot -Parent
$Venv = Join-Path $PumaRoot 'venv'

function Step($Text) { Write-Host "`n==> $Text" -ForegroundColor Cyan }

# Runs a program and stops the script when it fails, as native programs do not throw
function Run {
    & $args[0] @($args | Select-Object -Skip 1)
    if ($LASTEXITCODE -ne 0) { throw "Failed: $args" }
}

function Update-SessionPath {
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
        [Environment]::GetEnvironmentVariable('Path', 'User')
}

function Add-UserPath($Dir) {
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    if (($userPath -split ';') -notcontains $Dir) {
        [Environment]::SetEnvironmentVariable('Path', "$userPath;$Dir".TrimStart(';'), 'User')
    }
}

if ($env:VIRTUAL_ENV) { throw 'Deactivate your virtual environment first (run: deactivate).' }
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw 'winget is missing. Install "App Installer" from the Microsoft Store, then run this script again.'
}

Step 'Installing Python, Node.js, Tesseract and ffmpeg with winget'
$packages = @('Python.Python.3.12', 'UB-Mannheim.TesseractOCR', 'Gyan.FFmpeg')
# Node.js from another source works too, and a second installation would conflict with it
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { $packages += 'OpenJS.NodeJS.LTS' }
foreach ($id in $packages) {
    winget list --id $id --exact --accept-source-agreements | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Run winget install --id $id --exact --silent --accept-package-agreements --accept-source-agreements
    }
}

# Appium needs ANDROID_HOME to point to an Android SDK folder that contains platform-tools\adb.exe
$sdk = $env:ANDROID_HOME
if (-not $sdk) { $sdk = $env:ANDROID_SDK_ROOT }
if (-not $sdk) { $sdk = Join-Path $env:LOCALAPPDATA 'Android\Sdk' }
if (-not (Test-Path (Join-Path $sdk 'platform-tools\adb.exe'))) {
    Step "Installing adb in $sdk"
    $zip = Join-Path $env:TEMP 'platform-tools.zip'
    Invoke-WebRequest 'https://dl.google.com/android/repository/platform-tools-latest-windows.zip' -OutFile $zip -UseBasicParsing
    Expand-Archive $zip -DestinationPath $sdk -Force
    Remove-Item $zip
}

Step 'Setting ANDROID_HOME, and adding adb and Tesseract to the PATH'
foreach ($name in 'ANDROID_HOME', 'ANDROID_SDK_ROOT') {
    if (-not [Environment]::GetEnvironmentVariable($name)) {
        [Environment]::SetEnvironmentVariable($name, $sdk, 'User')
        Set-Item "env:$name" $sdk
    }
}
Add-UserPath (Join-Path $sdk 'platform-tools')
# The Tesseract installer does not add itself to the PATH
$tesseract = Join-Path $env:ProgramFiles 'Tesseract-OCR'
if (Test-Path $tesseract) { Add-UserPath $tesseract }
Update-SessionPath

Step 'Installing Appium and its driver'
if (-not (Get-Command appium -ErrorAction SilentlyContinue)) {
    Run npm install -g appium
    Update-SessionPath
}
# Through cmd, as Windows PowerShell turns output on stderr into an error
$installed = (cmd /c 'appium driver list --installed --json 2>nul') -join ''
if ($installed -notmatch '"uiautomator2"') { Run appium driver install uiautomator2 }

Step "Creating the virtual environment in $Venv"
if (-not (Test-Path $Venv)) { Run py -3.12 -m venv $Venv }
$python = Join-Path $Venv 'Scripts\python.exe'
Run $python -m pip install --upgrade pip
Run $python -m pip install -r (Join-Path $PumaRoot 'requirements.txt')

Step 'Installed versions'
Write-Host "Python:    $(& $python -V)"
Write-Host "adb:       $((& adb version)[0])"
Write-Host "Node.js:   $(& node -v)"
Write-Host "Appium:    $(& appium -v)"
Write-Host "Tesseract: $((cmd /c 'tesseract --version 2>&1')[0])"
Write-Host "ffmpeg:    $((& ffmpeg -version)[0])"

Write-Host @"

Puma is ready. Open a new terminal, so it picks up the new settings, and run:
  appium                              # keep this running while you use Puma
  $Venv\Scripts\Activate.ps1   # in a second terminal
"@
