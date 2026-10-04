@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo 源码运行需要 Python 3.12 和依赖，请先运行 setup_source.cmd。
  pause
  exit /b 1
)
".venv\Scripts\python.exe" "backend\launcher.py"
