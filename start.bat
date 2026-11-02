@echo off
rem Starts the Jarvis backend (port 8000) and frontend (port 3000), then opens the UI.
set NEXT_TELEMETRY_DISABLED=1
if not exist "%~dp0backend\.venv" (
  echo First run: creating Python environment...
  python -m venv "%~dp0backend\.venv"
  "%~dp0backend\.venv\Scripts\python" -m pip install -r "%~dp0backend\requirements.txt"
)
if not exist "%~dp0frontend\node_modules" (
  echo First run: installing frontend packages...
  pushd "%~dp0frontend" && call npm install && popd
)
if not exist "%~dp0frontend\.next" (
  pushd "%~dp0frontend" && call npm run build && popd
)
start "Jarvis backend" /D "%~dp0backend" ".venv\Scripts\python" -m uvicorn main:app --host 127.0.0.1 --port 8000
start "Jarvis frontend" /D "%~dp0frontend" cmd /c npm start
timeout /t 5 >nul
start http://127.0.0.1:3000
