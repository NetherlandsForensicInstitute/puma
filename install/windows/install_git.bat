@echo off

:: Check if Git is installed
where git >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo Git is not installed. Installing Git...

    IF NOT EXIST "git-installer.exe" (
        echo git-installer.exe not found. Downloading...
        :: Download Git installer
        powershell -Command "Invoke-WebRequest 'https://github.com/git-for-windows/git/releases/download/v2.49.0.windows.1/Git-2.49.0-64-bit.exe' -OutFile 'git-installer.exe'"
        set "downloaded_git=y"
    ) ELSE (
        echo git-installer.exe already exists. Skipping download.
    )

    :: Install Git
    echo Installing git...
    start /wait "" "git-installer.exe" /SILENT
    set "PATH=C:\Program Files\Git\cmd;%PATH%"

    :: Clean up
    IF defined downloaded_git (
        del git-installer.exe
    )

    echo Git installation completed.
) ELSE (
    echo Git is already installed.
)
