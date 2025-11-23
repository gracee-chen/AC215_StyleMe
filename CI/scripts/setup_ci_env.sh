#!/bin/bash
# Script to set up CI environment locally
# Usage: ./CI/scripts/setup_ci_env.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

cd "$PROJECT_ROOT"

echo -e "${BLUE}Setting up CI Environment${NC}"
echo "=============================="
echo ""

# Check Python version
echo -e "${GREEN}Checking Python version...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "Found: $PYTHON_VERSION"
else
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}Virtual environment created${NC}"
fi

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Upgrade pip
echo -e "${GREEN}Upgrading pip...${NC}"
pip install --upgrade pip

# Install development dependencies
echo -e "${GREEN}Installing development dependencies...${NC}"
pip install -r CI/requirements-dev.txt

# Install project dependencies
echo -e "${GREEN}Installing project dependencies...${NC}"
if [ -f "containers/training/requirements.txt" ]; then
    pip install -r containers/training/requirements.txt || echo -e "${YELLOW}Warning: Could not install training requirements${NC}"
fi

if [ -f "containers/inference/requirements.txt" ]; then
    pip install -r containers/inference/requirements.txt || echo -e "${YELLOW}Warning: Could not install inference requirements${NC}"
fi

if [ -f "containers/preprocessing/requirements.txt" ]; then
    pip install -r containers/preprocessing/requirements.txt || echo -e "${YELLOW}Warning: Could not install preprocessing requirements${NC}"
fi

# Verify installations
echo ""
echo -e "${GREEN}Verifying installations...${NC}"
if command -v pytest &> /dev/null; then
    echo -e "${GREEN}✓ pytest installed${NC}"
    pytest --version
else
    echo -e "${RED}✗ pytest not found${NC}"
fi

if command -v flake8 &> /dev/null; then
    echo -e "${GREEN}✓ flake8 installed${NC}"
    flake8 --version
else
    echo -e "${RED}✗ flake8 not found${NC}"
fi

echo ""
echo -e "${GREEN}Setup completed!${NC}"
echo ""
echo "You can now run:"
echo "  - ./CI/scripts/run_tests.sh    (run all tests)"
echo "  - ./CI/scripts/run_lint.sh     (run linting)"
echo ""

