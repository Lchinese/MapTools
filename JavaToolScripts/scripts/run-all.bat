@echo off
echo GPS Data Processor - Complete Workflow
echo ===========================================
echo.

REM Check if Java is installed
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Java is not installed or not added to PATH
    pause
    exit /b 1
)

REM Check if Maven is installed
mvn -v >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Maven is not installed or not added to PATH
    pause
    exit /b 1
)

echo [1/3] Compiling project...
call mvn clean compile
if %errorlevel% neq 0 (
    echo Error occurred during compilation!
    pause
    exit /b 1
)
echo Project compilation completed!
echo.

echo [2/3] Building JAR package...
call mvn package -DskipTests
if %errorlevel% neq 0 (
    echo Error occurred during building!
    pause
    exit /b 1
)
echo JAR package building completed!
echo.

echo [3/3] Running GPS Data Processor...
set DATA_DIR=data
if "%~1" neq "" (
    set DATA_DIR=%~1
)

echo Processing GPS data, data directory: %DATA_DIR%
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

echo.
echo All steps completed!
pause