#!/usr/bin/env python
"""
Run Book Factory tests from the project root directory
This script is a simple wrapper around the test scripts in the test directory
"""
import os
import sys
import subprocess
import argparse

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Run Book Factory tests")
    parser.add_argument("--test", choices=["outline", "chapter-outline", "write", "flow", "all", "programmatic"],
                        default="all", help="Test to run")
    parser.add_argument("--chapter", type=int, default=1,
                        help="Chapter number for chapter-specific tests")
    parser.add_argument("--force", action="store_true",
                        help="Force regeneration of chapters")
    
    args = parser.parse_args()
    
    # Ensure we're in the project root directory
    if not os.path.exists("test"):
        print("Error: test directory not found. Make sure you're running this script from the project root directory.")
        sys.exit(1)
    
    # Get Python executable
    python_exe = sys.executable
    
    # Determine which script to run
    if args.test == "all":
        cmd = [python_exe, "test/run_all_tests.py"]
        if args.chapter != 1:
            cmd.extend(["--chapter", str(args.chapter)])
        if args.force:
            cmd.append("--force")
    elif args.test == "programmatic":
        cmd = [python_exe, "test/programmatic_book_cli_example.py"]
    else:
        cmd = [python_exe, "test/quick_test.py", args.test]
        if args.test in ["chapter-outline", "write", "flow"]:
            cmd.extend(["--chapter", str(args.chapter)])
        if args.force and args.test == "write":
            cmd.append("--force")
    
    # Run the command
    print(f"Running command: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        print("Test completed successfully")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"Test failed with exit code: {e.returncode}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()