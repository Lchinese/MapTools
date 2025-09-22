@echo off
echo Building Java GPS Data Processor...
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

REM Build project
echo Building project...
call mvn clean package

if %errorlevel% equ 0 (
    echo.
    echo Build successful!
    echo JAR file created in target/ directory
    echo File location: %cd%\target\gps-data-processor-1.0-SNAPSHOT.jar
) else (
    echo.
    echo Build failed!
    pause
    exit /b 1
)

pause