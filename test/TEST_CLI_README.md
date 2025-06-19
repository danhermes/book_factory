# Book Factory CLI Testing

This directory contains scripts for testing the Book Factory CLI functionality. All test scripts are designed to work from within the `test` directory and reference the `book_cli.py` file in the parent directory.

## Overview

The Book Factory is a system for automated book generation using AI agents organized in "crews". The CLI provides a command-line interface for interacting with this system.

## Directory Structure

```
book_factory/
├── book_cli.py             # Main CLI entry point
├── run_chapter.py          # Script for running a single chapter
├── test/                   # Test directory (you are here)
│   ├── test_book_cli.py    # Main test script
│   ├── test_book_cli.sh    # Shell script for Linux/macOS
│   ├── test_book_cli.bat   # Batch script for Windows
│   ├── quick_test.py       # Quick test script
│   ├── run_all_tests.py    # Script to run all tests
│   └── ...                 # Other test files
└── ...                     # Other project files
```

## Test Scripts

### `test_book_cli.py`

A Python script that tests various aspects of the Book Factory CLI:

- Generating a full book outline
- Generating an outline for a specific chapter
- Writing content for a specific chapter
- Running the full book generation flow

#### Usage

```bash
# Run all tests using chapter 1
python ./test_book_cli.py

# Generate just the outline
python ./test_book_cli.py --test outline

# Generate outline for a specific chapter
python ./test_book_cli.py --test chapter-outline --chapter 3

# Write a specific chapter
python ./test_book_cli.py --test write --chapter 2

# Force regeneration of a chapter even if it exists
python ./test_book_cli.py --test write --chapter 2 --force

# Run the full flow for a specific chapter
python ./test_book_cli.py --test flow --chapter 3
```

Note: All scripts reference the `book_cli.py` file in the parent directory using relative paths (`../book_cli.py`).

### `test_book_cli.sh` (Linux/macOS)

A shell script that provides an interactive menu for running the tests:

1. Generate full book outline
2. Generate outline for a specific chapter
3. Write a specific chapter
4. Run full book flow for a specific chapter
5. Run all tests

#### Usage

```bash
# Make the script executable
chmod +x test_book_cli.sh

# Run the script
./test_book_cli.sh
```

### `test_book_cli.bat` (Windows)

A batch script that provides the same interactive menu for Windows users:

1. Generate full book outline
2. Generate outline for a specific chapter
3. Write a specific chapter
4. Run full book flow for a specific chapter
5. Run all tests

#### Usage

```cmd
# Run the batch file
test_book_cli.bat
```

### `programmatic_book_cli_example.py`

An example of how to use the Book Factory CLI programmatically from another Python script:

- Demonstrates how to integrate book generation into your own applications
- Provides a `BookGenerator` class with methods for all CLI operations
- Includes example usage code

#### Usage

```bash
# Run the example
python ./programmatic_book_cli_example.py
```

### `quick_test.py`

A simple command-line script for quickly running a specific test:

- Provides a straightforward interface for testing specific functionality
- Includes validation of output files
- Reports test success/failure and execution time

#### Usage

```bash
# Generate the book outline
python ./quick_test.py outline

# Generate outline for chapter 3
python ./quick_test.py chapter-outline --chapter 3

# Write chapter 2
python ./quick_test.py write --chapter 2

# Force regeneration of chapter 2
python ./quick_test.py write --chapter 2 --force

# Run the full flow for chapter 1
python ./quick_test.py flow --chapter 1
```

### `run_all_tests.py`

A comprehensive script that can run multiple tests in sequence:

- Allows running all tests or a specific subset
- Provides a summary of test results
- Reports total execution time and individual test status

#### Usage

```bash
# Run all tests
python ./run_all_tests.py

# Run specific tests
python ./run_all_tests.py --tests outline,write

# Run tests for a specific chapter
python ./run_all_tests.py --chapter 3

# Force regeneration of chapters
python ./run_all_tests.py --force

# Run specific tests for a specific chapter with force
python ./run_all_tests.py --tests write,flow --chapter 2 --force
```

## Output

The test scripts will create output in the following directories (relative to the project root):

- `output/outlines/` - Book outline files (JSON and Markdown)
- `output/chapters/` - Generated chapter content
- `output/research/` - Research content used for chapter generation
- `output/analysis/` - Analysis reports (when using analyze_test_results.py)

## Example Workflow

A typical workflow for testing the Book Factory might be:

1. Generate the book outline
2. Check the outline files to ensure they look correct
3. Generate a single chapter to test the content generation
4. If everything looks good, run the full flow for all chapters

## Programmatic Integration

If you want to integrate the Book Factory into your own applications:

1. Use the `BookGenerator` class from `test/programmatic_book_cli_example.py` as a starting point
2. Customize the methods to fit your specific requirements
3. Add error handling appropriate for your application
4. Consider adding asynchronous support for long-running operations

## Troubleshooting

If you encounter issues:

1. Check the log output for error messages
2. Ensure all required dependencies are installed
3. Verify that the necessary configuration files exist
4. Check that the output directories are writable

## System Requirements

- Python 3.8 or higher
- CrewAI and its dependencies
- Sufficient disk space for output files

## Installation

To install the required dependencies:

```bash
# Install from the requirements file
pip install -r ./test_requirements.txt
```

The `test_requirements.txt` file includes:

- Core dependencies (crewai, pydantic, python-dotenv)
- Testing dependencies (pytest, pytest-cov)
- Utility dependencies (colorama, tqdm)