@echo off
echo Compiling Java GPS Data Processor...
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

REM Compile project
echo Compiling project...
call mvn clean compile

if %errorlevel% equ 0 (
    echo.
    echo Compilation successful!
) else (
    echo.
    echo Compilation failed!
    pause
    exit /b 1
)

pause