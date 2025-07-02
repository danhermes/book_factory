# Book Factory Testing Guide

This document provides information on how to test the Book Factory CLI.

## Quick Start

You can run tests using one of the following methods:

### Using Python

```bash
# Run all tests
python run_tests.py

# Run a specific test
python run_tests.py --test outline

# Run a test for a specific chapter
python run_tests.py --test write --chapter 3

# Force regeneration of a chapter
python run_tests.py --test write --chapter 3 --force
```

### Using Shell Script (Linux/macOS)

```bash
# Make the script executable
chmod +x run_tests.sh

# Run the script
./run_tests.sh
```

### Using Batch Script (Windows)

```cmd
# Run the batch file
run_tests.bat
```

## Test Directory

All test scripts are located in the `test` directory. The main scripts are:

- `test_book_cli.py` - Main test script
- `quick_test.py` - Quick test script
- `run_all_tests.py` - Script to run all tests
- `programmatic_book_cli_example.py` - Example of programmatic usage
- `analyze_test_results.py` - Script to analyze test results

## Available Tests

1. **Outline Test**: Generates a full book outline
   ```bash
   python run_tests.py --test outline
   ```

2. **Chapter Outline Test**: Generates an outline for a specific chapter
   ```bash
   python run_tests.py --test chapter-outline --chapter 3
   ```

3. **Write Test**: Writes content for a specific chapter
   ```bash
   python run_tests.py --test write --chapter 2
   ```

4. **Flow Test**: Runs the full book generation flow for a specific chapter
   ```bash
   python run_tests.py --test flow --chapter 1
   ```

5. **Programmatic Example**: Runs the programmatic example
   ```bash
   python run_tests.py --test programmatic
   ```

## Output

The test scripts will create output in the following directories:

- `output/outlines/` - Book outline files (JSON and Markdown)
- `output/chapters/` - Generated chapter content
- `output/research/` - Research content used for chapter generation
- `output/analysis/` - Analysis reports (when using analyze_test_results.py)

## Detailed Documentation

For more detailed documentation on the test scripts, see:

- [Test Directory README](./test/README.md)
- [Detailed Test Documentation](./test/TEST_CLI_README.md)

## Requirements

To run the tests, you need:

- Python 3.8 or higher
- CrewAI and its dependencies

You can install the required dependencies using:

```bash
pip install -r test/test_requirements.txt