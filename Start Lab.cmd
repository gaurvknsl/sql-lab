@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
  py -3 start.py %*
) else (
  where python >nul 2>nul
  if not errorlevel 1 (
    python start.py %*
  ) else (
    echo Python 3.10 or newer is required.
    echo Install it from https://www.python.org/downloads/ and reopen this launcher.
    echo Enable the Python launcher or Add Python to PATH during installation.
    pause
    exit /b 1
  )
)
set "SQL_LAB_EXIT=%ERRORLEVEL%"
if not "%SQL_LAB_EXIT%"=="0" (
  echo.
  echo The lab did not start. Read the message above for details.
  pause
)
exit /b %SQL_LAB_EXIT%
