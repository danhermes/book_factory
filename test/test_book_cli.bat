@echo off
REM Simple batch script to run test_book_cli.py with different options
setlocal enabledelayedexpansion

echo === Book Factory CLI Test Script ===
echo.

REM Check if Python is available
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

REM Check if the test script exists
if not exist "test_book_cli.py" (
    echo Error: test_book_cli.py not found in current directory
    exit /b 1
)

REM Display menu
echo Select a test to run:
echo 1) Generate full book outline
echo 2) Generate outline for a specific chapter
echo 3) Write a specific chapter
echo 4) Run full book flow for a specific chapter
echo 5) Run all tests
echo q) Quit
echo.

set /p choice="Enter your choice (1-5, q): "

if "%choice%"=="1" (
    call :run_test "python test_book_cli.py --test outline" "Generate full book outline"
) else if "%choice%"=="2" (
    set /p chapter="Enter chapter number: "
    call :run_test "python test_book_cli.py --test chapter-outline --chapter !chapter!" "Generate outline for chapter !chapter!"
) else if "%choice%"=="3" (
    set /p chapter="Enter chapter number: "
    set /p force="Force regeneration? (y/n): "
    if "!force!"=="y" (
        call :run_test "python test_book_cli.py --test write --chapter !chapter! --force" "Write chapter !chapter! (force)"
    ) else (
        call :run_test "python test_book_cli.py --test write --chapter !chapter!" "Write chapter !chapter!"
    )
) else if "%choice%"=="4" (
    set /p chapter="Enter chapter number: "
    call :run_test "python test_book_cli.py --test flow --chapter !chapter!" "Run full flow for chapter !chapter!"
) else if "%choice%"=="5" (
    set /p chapter="Enter chapter number for tests: "
    set /p force="Force regeneration? (y/n): "
    if "!force!"=="y" (
        call :run_test "python test_book_cli.py --test all --chapter !chapter! --force" "Run all tests for chapter !chapter! (force)"
    ) else (
        call :run_test "python test_book_cli.py --test all --chapter !chapter!" "Run all tests for chapter !chapter!"
    )
) else if "%choice%"=="q" (
    echo Exiting...
    exit /b 0
) else (
    echo Invalid choice
    exit /b 1
)

echo === Test script completed ===
exit /b 0

:run_test
echo Running: %~2
echo Command: %~1
echo.

%~1

if %ERRORLEVEL% equ 0 (
    echo Test completed successfully
) else (
    echo Test failed
)
echo.
exit /b 0