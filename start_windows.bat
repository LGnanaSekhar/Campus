@echo off
setlocal
cd /d "%~dp0"
echo PULSEIQ React + FastAPI local launcher
where py >nul 2>nul || (echo Install Python 3.12 first & pause & exit /b 1)
where npm >nul 2>nul || (echo Install Node.js and npm first & pause & exit /b 1)
if "%DATABASE_URL%"=="" (
  echo ERROR: Set DATABASE_URL in this Command Prompt to the Supabase Session pooler URI first.
  echo Also set APP_SECRET, BOOTSTRAP_COLLEGE_NAME, BOOTSTRAP_COLLEGE_DOMAIN,
  echo BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD.
  pause
  exit /b 1
)
if not exist .venv\Scripts\python.exe py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-connectors.txt
if errorlevel 1 (pause & exit /b 1)
if not exist frontend\node_modules (
  pushd frontend
  call npm ci
  popd
  if errorlevel 1 (pause & exit /b 1)
)
set COOKIE_SECURE=false
start "PULSEIQ API" cmd /k ".venv\Scripts\python.exe -m uvicorn backend.main:create_app --factory --host 127.0.0.1 --port 8000"
start "PULSEIQ React" cmd /k "cd frontend && npm run dev"
echo Local site: http://127.0.0.1:5173
pause
