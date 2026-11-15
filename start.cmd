@echo off
setlocal
cd /d "%~dp0"
call "Start Lab.cmd" --mode dsa %*
