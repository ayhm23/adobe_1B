@echo off
REM Adobe 1B Challenge - Docker Runner Script (Windows)
REM This script helps you run the Docker container with the correct volume mounts

echo ==========================================
echo Adobe 1B Challenge - Docker Runner
echo ==========================================

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not installed or not in PATH
    pause
    exit /b 1
)

REM Get the current directory
set WORKSPACE_DIR=%CD%
echo Workspace directory: %WORKSPACE_DIR%

REM Create output directory if it doesn't exist
if not exist "docker_output" mkdir docker_output

REM Check if Dockerfile exists
if not exist "Dockerfile" (
    echo Error: Dockerfile not found. Please run this script from the project root directory.
    pause
    exit /b 1
)

REM Build the Docker image
echo.
echo Building Docker image...
echo Note: Use --build-arg CACHE_BUST=%date% to force model re-download
docker build -t adobe1b-solution .

REM Check if Challenge_1b directory exists
if exist "Challenge_1b" (
    echo.
    echo Found Challenge_1b directory with collections:
    for /d %%d in ("Challenge_1b\Collection*") do (
        echo   - %%~nd
    )
    
    echo.
    echo Running Docker container with full workspace mount...
    echo This will allow access to all collections.
    
    docker run -it -v "%WORKSPACE_DIR%:/app" -v "%WORKSPACE_DIR%/docker_output:/app/output" adobe1b-solution
    
) else (
    echo.
    echo Challenge_1b directory not found.
    echo Please ensure you're running this from the correct directory or
    echo mount your PDF directory manually using:
    echo.
    echo   docker run -it -v /path/to/pdfs:/app/data -v "%WORKSPACE_DIR%/docker_output:/app/output" adobe1b-solution
)

pause
