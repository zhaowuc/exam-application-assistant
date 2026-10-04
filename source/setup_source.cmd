@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -m venv .venv
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements-lock.txt
if errorlevel 1 goto failed
echo 后端环境已准备就绪。已附带前端构建产物，可运行 start_source.cmd。
pause
exit /b 0
:failed
echo 环境初始化失败。请确认已安装 Python 3.12，首次安装开发依赖需要网络。
pause
exit /b 1
