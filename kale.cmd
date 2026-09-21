@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "PYTHONPATH=%SCRIPT_DIR%src;%PYTHONPATH%"
"%SCRIPT_DIR%.venv\Scripts\kale.exe" %*
