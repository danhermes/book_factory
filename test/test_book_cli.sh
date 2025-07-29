#!/bin/bash
# Simple shell script to run test_book_cli.py with different options

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Book Factory CLI Test Script ===${NC}"
echo ""

# Function to run a test with a description
run_test() {
    local cmd="$1"
    local description="$2"
    
    echo -e "${YELLOW}Running: ${description}${NC}"
    echo -e "${BLUE}Command: ${cmd}${NC}"
    echo ""
    
    eval $cmd
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Test completed successfully${NC}"
    else
        echo -e "${RED}❌ Test failed${NC}"
    fi
    echo ""
}

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo -e "${RED}Error: Python is not installed or not in PATH${NC}"
    exit 1
fi

# Check if the test script exists
if [ ! -f "test_book_cli.py" ]; then
    echo -e "${RED}Error: test_book_cli.py not found in current directory${NC}"
    exit 1
fi

# Make the test script executable
chmod +x test_book_cli.py

# Display menu
echo "Select a test to run:"
echo "1) Generate full book outline"
echo "2) Generate outline for a specific chapter"
echo "3) Write a specific chapter"
echo "4) Run full book flow for a specific chapter"
echo "5) Run all tests"
echo "q) Quit"
echo ""

read -p "Enter your choice (1-5, q): " choice

case $choice in
    1)
        run_test "python test_book_cli.py --test outline" "Generate full book outline"
        ;;
    2)
        read -p "Enter chapter number: " chapter
        run_test "python test_book_cli.py --test chapter-outline --chapter $chapter" "Generate outline for chapter $chapter"
        ;;
    3)
        read -p "Enter chapter number: " chapter
        read -p "Force regeneration? (y/n): " force
        if [ "$force" = "y" ]; then
            run_test "python test_book_cli.py --test write --chapter $chapter --force" "Write chapter $chapter (force)"
        else
            run_test "python test_book_cli.py --test write --chapter $chapter" "Write chapter $chapter"
        fi
        ;;
    4)
        read -p "Enter chapter number: " chapter
        run_test "python test_book_cli.py --test flow --chapter $chapter" "Run full flow for chapter $chapter"
        ;;
    5)
        read -p "Enter chapter number for tests: " chapter
        read -p "Force regeneration? (y/n): " force
        if [ "$force" = "y" ]; then
            run_test "python test_book_cli.py --test all --chapter $chapter --force" "Run all tests for chapter $chapter (force)"
        else
            run_test "python test_book_cli.py --test all --chapter $chapter" "Run all tests for chapter $chapter"
        fi
        ;;
    q|Q)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo -e "${BLUE}=== Test script completed ===${NC}"