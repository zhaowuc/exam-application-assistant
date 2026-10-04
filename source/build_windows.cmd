@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe goto failed
where node >nul 2>nul
if errorlevel 1 goto failed
cd frontend
if not exist node_modules\vite\bin\vite.js (
  echo 请先安装 Node.js 和 pnpm，并在 frontend 中运行 pnpm install --frozen-lockfile。
  goto failed
)
node node_modules\vite\bin\vite.js build
if errorlevel 1 goto failed
cd ..
.venv\Scripts\python.exe backend\manage.py test core
if errorlevel 1 goto failed
.venv\Scripts\python.exe -m PyInstaller --noconfirm build_portable.spec
if errorlevel 1 goto failed
.venv\Scripts\python.exe qa\package_release.py
if errorlevel 1 goto failed
echo 离线包已生成到 source 上级目录。
pause
exit /b 0
:failed
echo 构建失败。请查看上方错误并参考 source\README.md。
pause
exit /b 1
