@echo off
echo ========================================
echo   Starting Policy Q&A System
echo ========================================
echo.

REM Check if .env exists
if not exist .env (
    echo Creating .env from env.example...
    copy env.example .env
    echo.
    echo WARNING: Please edit .env and add your API keys:
    echo   - EMBEDDING__API_KEY
    echo   - STARGATE_API_KEY
    echo   - STARGATE_BASE_URL
    echo.
    pause
)

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo Starting Docker services...
echo.

docker-compose up -d --build

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start services!
    echo Check Docker Desktop is running and try again.
    pause
    exit /b 1
)

echo.
echo Waiting for services to start (30 seconds)...
timeout /t 30 /nobreak >nul

echo.
echo ========================================
echo   Service Status
echo ========================================
docker-compose ps

echo.
echo ========================================
echo   Health Checks
echo ========================================
echo.
echo Checking API health...
curl -s http://localhost:8000/health || echo API not ready yet

echo.
echo Checking UI health...
curl -s http://localhost:8501/_stcore/health || echo UI not ready yet

echo.
echo ========================================
echo   Access URLs
echo ========================================
echo.
echo Streamlit UI:  http://localhost:8501
echo FastAPI API:   http://localhost:8000
echo LiteLLM Proxy: http://localhost:4000
echo.
echo ========================================
echo.
echo Services are starting! Open http://localhost:8501 in your browser.
echo.
echo To view logs: docker-compose logs -f
echo To stop:      docker-compose down
echo.
pause
