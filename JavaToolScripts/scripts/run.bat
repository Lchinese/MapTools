@echo off
setlocal

echo Running GPS Data Processor...
echo.

REM Check if Java is installed
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Java is not installed or not added to PATH
    pause
    exit /b 1
)

REM Check if JAR file exists
if not exist "target\gps-data-processor-1.0-SNAPSHOT.jar" (
    echo Error: JAR file not found. Please build the project using build.bat first
    pause
    exit /b 1
)

REM Set default data directory (if no argument provided)
set DATA_DIR=data
if "%~1" neq "" (
    set DATA_DIR=%~1
)

echo Processing GPS data, data directory: %DATA_DIR%
echo.

REM Run the application
java -jar target/gps-data-processor-1.0-SNAPSHOT.jar "%DATA_DIR%"

if %errorlevel% equ 0 (
    echo.
    echo GPS data processing completed!
) else (
    echo.
    echo GPS data processing failed!
    pause
    exit /b 1
)

pause