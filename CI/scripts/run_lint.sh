#!/bin/bash
# Script to run linting locally
# Usage: ./CI/scripts/run_lint.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Check if flake8 is installed
if ! command -v flake8 &> /dev/null; then
    echo -e "${RED}Error: flake8 is not installed${NC}"
    echo "Install it with: pip install -r CI/requirements-dev.txt"
    echo "Or run: ./CI/scripts/setup_ci_env.sh"
    exit 1
fi

echo -e "${GREEN}Running Flake8 Linting${NC}"
echo "=========================="
echo ""

# Run flake8 with CI config
echo -e "${GREEN}Linting src/ directory...${NC}"
flake8 src/ --config=CI/config/.flake8

echo -e "${GREEN}Linting containers/ directory...${NC}"
flake8 containers/ --config=CI/config/.flake8

echo -e "${GREEN}Linting scripts/ directory...${NC}"
flake8 scripts/ --config=CI/config/.flake8

echo ""
echo -e "${GREEN}Linting completed!${NC}"
echo -e "${GREEN}No issues found.${NC}"

