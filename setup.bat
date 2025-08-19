@echo off
setlocal enabledelayedexpansion

REM AgentFlow Setup Script for Windows
REM Multi-Agent AI System for Automated Documentation and Testing

echo.
echo ========================================
echo         AgentFlow Setup Script
echo ========================================
echo.
echo This script will set up the AgentFlow system
echo.

REM Check if Docker is running
echo [INFO] Checking if Docker is running...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)
echo [SUCCESS] Docker is running

REM Check if Docker Compose is available
echo [INFO] Checking Docker Compose...
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose not found. Please install Docker Compose.
    pause
    exit /b 1
)
echo [SUCCESS] Docker Compose found

REM Create project structure
echo [INFO] Creating project structure...
if not exist "laravel-app\storage" mkdir "laravel-app\storage"
if not exist "laravel-app\storage\app" mkdir "laravel-app\storage\app"
if not exist "laravel-app\storage\framework" mkdir "laravel-app\storage\framework"
if not exist "laravel-app\storage\logs" mkdir "laravel-app\storage\logs"
if not exist "laravel-app\bootstrap\cache" mkdir "laravel-app\bootstrap\cache"
if not exist "python-agents\logs" mkdir "python-agents\logs"
if not exist "python-agents\.cache" mkdir "python-agents\.cache"
echo [SUCCESS] Project structure created

REM Setup environment
echo [INFO] Setting up environment...
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo [SUCCESS] Environment file created from template
    ) else (
        echo [ERROR] .env.example not found!
        pause
        exit /b 1
    )
) else (
    echo [WARNING] .env file already exists, skipping...
)

REM Configure AgentFlow
echo [INFO] Configuring AgentFlow...
if not exist ".agentflow.yaml" (
    if exist "config\agentflow.yaml.example" (
        copy "config\agentflow.yaml.example" ".agentflow.yaml" >nul
        echo [SUCCESS] AgentFlow configuration created from template
    ) else (
        echo [WARNING] AgentFlow configuration template not found, skipping...
    )
) else (
    echo [WARNING] .agentflow.yaml already exists, skipping...
)

REM Start Docker services
echo [INFO] Starting Docker services...
echo [INFO] Building Docker images...
docker-compose -f docker\docker-compose.yml build

echo [INFO] Starting services...
docker-compose -f docker\docker-compose.yml up -d

echo [INFO] Waiting for services to be ready...
timeout /t 30 /nobreak >nul

REM Check service health
echo [INFO] Checking service health...
docker-compose -f docker\docker-compose.yml ps

echo.
echo ========================================
echo         Setup Completed!
echo ========================================
echo.
echo Next steps:
echo 1. Open your browser and navigate to: http://localhost:8000
echo 2. Create your first project
echo 3. Upload some PHP files or connect a Git repository
echo 4. Watch the AI agents analyze your code!
echo.
echo Useful commands:
echo • View logs: docker-compose -f docker\docker-compose.yml logs -f
echo • Stop services: docker-compose -f docker\docker-compose.yml down
echo • Restart services: docker-compose -f docker\docker-compose.yml restart
echo • View running containers: docker-compose -f docker\docker-compose.yml ps
echo.
echo Configuration:
echo • Edit .env file to customize environment variables
echo • Edit .agentflow.yaml to customize AI agent behavior
echo • Check docker\docker-compose.yml for service configuration
echo.
echo Important:
echo • Make sure to set your OPENROUTER_API_KEY in the .env file
echo • The system will not work without a valid API key
echo.
pause
