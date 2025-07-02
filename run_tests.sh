#!/bin/bash
# Simple shell script to run Book Factory tests from the project root directory

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Book Factory Test Runner ===${NC}"
echo ""

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo -e "${RED}Error: Python is not installed or not in PATH${NC}"
    exit 1
fi

# Check if the test directory exists
if [ ! -d "test" ]; then
    echo -e "${RED}Error: test directory not found. Make sure you're running this script from the project root directory.${NC}"
    exit 1
fi

# Display menu
echo "Select a test to run:"
echo "1) Generate full book outline"
echo "2) Generate outline for a specific chapter"
echo "3) Write a specific chapter"
echo "4) Run full book flow for a specific chapter"
echo "5) Run all tests"
echo "6) Run programmatic example"
echo "q) Quit"
echo ""

read -p "Enter your choice (1-6, q): " choice

case $choice in
    1)
        python test/quick_test.py outline
        ;;
    2)
        read -p "Enter chapter number: " chapter
        python test/quick_test.py chapter-outline --chapter $chapter
        ;;
    3)
        read -p "Enter chapter number: " chapter
        read -p "Force regeneration? (y/n): " force
        if [ "$force" = "y" ]; then
            python test/quick_test.py write --chapter $chapter --force
        else
            python test/quick_test.py write --chapter $chapter
        fi
        ;;
    4)
        read -p "Enter chapter number: " chapter
        python test/quick_test.py flow --chapter $chapter
        ;;
    5)
        read -p "Enter chapter number for tests: " chapter
        read -p "Force regeneration? (y/n): " force
        if [ "$force" = "y" ]; then
            python test/run_all_tests.py --chapter $chapter --force
        else
            python test/run_all_tests.py --chapter $chapter
        fi
        ;;
    6)
        python test/programmatic_book_cli_example.py
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

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Test completed successfully${NC}"
else
    echo -e "${RED}❌ Test failed${NC}"
fi

echo -e "${BLUE}=== Test completed ===${NC}"