#!/usr/bin/env python
"""
Run all Book Factory CLI tests in sequence
This script allows running multiple tests in a single execution
"""
import argparse
import logging
import os
import subprocess
import sys
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("run_all_tests")

def run_command(cmd, description):
    """Run a command and log the result"""
    logger.info(f"Running: {description}")
    logger.info(f"Command: {' '.join(cmd)}")
    
    start_time = time.time()
    try:
        result = subprocess.run(cmd, check=True)
        success = True
        logger.info(f"Command completed successfully with exit code: {result.returncode}")
    except subprocess.CalledProcessError as e:
        success = False
        logger.error(f"Command failed with exit code: {e.returncode}")
    
    elapsed_time = time.time() - start_time
    logger.info(f"Completed in {elapsed_time:.2f} seconds")
    
    return success

def run_tests(tests, chapter=1, force=False):
    """Run the specified tests"""
    results = {}
    
    # Ensure output directories exist
    os.makedirs("output/outlines", exist_ok=True)
    os.makedirs("output/chapters", exist_ok=True)
    os.makedirs("output/research", exist_ok=True)
    
    # Get Python executable
    python_exe = sys.executable
    
    # Determine the path to the test scripts
    script_dir = os.path.dirname(os.path.abspath(__file__))
    quick_test_path = os.path.join(script_dir, "quick_test.py")
    programmatic_example_path = os.path.join(script_dir, "programmatic_book_cli_example.py")
    
    # Make sure the paths exist
    if not os.path.exists(quick_test_path):
        logger.error(f"quick_test.py not found at {quick_test_path}")
        return {}
    
    if not os.path.exists(programmatic_example_path):
        logger.error(f"programmatic_book_cli_example.py not found at {programmatic_example_path}")
        return {}
    
    logger.info(f"Using quick_test.py at: {quick_test_path}")
    logger.info(f"Using programmatic_book_cli_example.py at: {programmatic_example_path}")
    
    # Run each test
    for test in tests:
        logger.info(f"=== RUNNING TEST: {test} ===")
        
        if test == "outline":
            cmd = [python_exe, quick_test_path, "outline"]
            success = run_command(cmd, "Generate book outline")
            results["outline"] = success
            
        elif test == "chapter-outline":
            cmd = [python_exe, quick_test_path, "chapter-outline", "--chapter", str(chapter)]
            success = run_command(cmd, f"Generate outline for chapter {chapter}")
            results["chapter-outline"] = success
            
        elif test == "write":
            cmd = [python_exe, quick_test_path, "write", "--chapter", str(chapter)]
            if force:
                cmd.append("--force")
            success = run_command(cmd, f"Write chapter {chapter}" + (" (force)" if force else ""))
            results["write"] = success
            
        elif test == "flow":
            cmd = [python_exe, quick_test_path, "flow", "--chapter", str(chapter)]
            success = run_command(cmd, f"Run full flow for chapter {chapter}")
            results["flow"] = success
            
        elif test == "programmatic":
            cmd = [python_exe, programmatic_example_path]
            success = run_command(cmd, "Run programmatic example")
            results["programmatic"] = success
            
        else:
            logger.warning(f"Unknown test: {test}")
    
    return results

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Run all Book Factory CLI tests")
    parser.add_argument("--tests", type=str, default="all",
                        help="Tests to run (comma-separated: outline,chapter-outline,write,flow,programmatic or 'all')")
    parser.add_argument("--chapter", type=int, default=1,
                        help="Chapter number for tests (default: 1)")
    parser.add_argument("--force", action="store_true",
                        help="Force regeneration of chapters")
    
    args = parser.parse_args()
    
    # Determine which tests to run
    if args.tests.lower() == "all":
        tests = ["outline", "chapter-outline", "write", "flow", "programmatic"]
    else:
        tests = [test.strip() for test in args.tests.split(",")]
    
    logger.info(f"Running tests: {', '.join(tests)}")
    logger.info(f"Chapter: {args.chapter}")
    logger.info(f"Force: {args.force}")
    
    # Run the tests
    start_time = time.time()
    results = run_tests(tests, args.chapter, args.force)
    elapsed_time = time.time() - start_time
    
    # Print summary
    logger.info("=== TEST SUMMARY ===")
    logger.info(f"Total time: {elapsed_time:.2f} seconds")
    
    all_success = True
    for test, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"{test}: {status}")
        if not success:
            all_success = False
    
    if all_success:
        logger.info("All tests passed successfully!")
        sys.exit(0)
    else:
        logger.error("Some tests failed. See log for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()