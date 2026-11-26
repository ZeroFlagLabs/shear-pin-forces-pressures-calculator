@echo off
setlocal
set "ROOT=%~dp0.."
set "PY=%ROOT%\.venv\Scripts\python.exe"
if not exist "%PY%" (
 echo Development environment missing: "%PY%"
 pause
 exit /b 1
)
"%PY%" -B "%ROOT%\src\main.py" %*
if errorlevel 1 pause
