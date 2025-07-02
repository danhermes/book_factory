@echo off
REM Simple batch script to run Book Factory tests from the project root directory
setlocal enabledelayedexpansion

echo === Book Factory Test Runner ===
echo.

REM Check if Python is available
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

REM Check if the test directory exists
if not exist "test" (
    echo Error: test directory not found. Make sure you're running this script from the project root directory.
    exit /b 1
)

REM Display menu
echo Select a test to run:
echo 1) Generate full book outline
echo 2) Generate outline for a specific chapter
echo 3) Write a specific chapter
echo 4) Run full book flow for a specific chapter
echo 5) Run all tests
echo 6) Run programmatic example
echo q) Quit
echo.

set /p choice="Enter your choice (1-6, q): "

if "%choice%"=="1" (
    python test\quick_test.py outline
) else if "%choice%"=="2" (
    set /p chapter="Enter chapter number: "
    python test\quick_test.py chapter-outline --chapter !chapter!
) else if "%choice%"=="3" (
    set /p chapter="Enter chapter number: "
    set /p force="Force regeneration? (y/n): "
    if "!force!"=="y" (
        python test\quick_test.py write --chapter !chapter! --force
    ) else (
        python test\quick_test.py write --chapter !chapter!
    )
) else if "%choice%"=="4" (
    set /p chapter="Enter chapter number: "
    python test\quick_test.py flow --chapter !chapter!
) else if "%choice%"=="5" (
    set /p chapter="Enter chapter number for tests: "
    set /p force="Force regeneration? (y/n): "
    if "!force!"=="y" (
        python test\run_all_tests.py --chapter !chapter! --force
    ) else (
        python test\run_all_tests.py --chapter !chapter!
    )
) else if "%choice%"=="6" (
    python test\programmatic_book_cli_example.py
) else if "%choice%"=="q" (
    echo Exiting...
    exit /b 0
) else (
    echo Invalid choice
    exit /b 1
)

if %ERRORLEVEL% equ 0 (
    echo Test completed successfully
) else (
    echo Test failed
)

echo === Test completed ===