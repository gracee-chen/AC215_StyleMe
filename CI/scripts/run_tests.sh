#!/bin/bash
# Script to run all tests locally
# Usage: ./CI/scripts/run_tests.sh [unit|integration|e2e|all]

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

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest is not installed${NC}"
    echo "Install it with: pip install -r CI/requirements-dev.txt"
    echo "Or run: ./CI/scripts/setup_ci_env.sh"
    exit 1
fi

# Parse arguments
TEST_TYPE="${1:-all}"

echo -e "${GREEN}Running StyleMe CI Tests${NC}"
echo "=================================="
echo ""

# Run tests based on type
case "$TEST_TYPE" in
    unit)
        echo -e "${GREEN}Running unit tests...${NC}"
        pytest CI/tests/ -m unit -v --tb=short --cov=src --cov=containers --cov-config=CI/config/.coveragerc -c CI/config/pytest.ini
        ;;
    integration)
        echo -e "${GREEN}Running integration tests...${NC}"
        pytest CI/tests/integration/ -m integration -v --tb=short --cov=src --cov=containers --cov-config=CI/config/.coveragerc -c CI/config/pytest.ini
        ;;
    e2e)
        echo -e "${GREEN}Running end-to-end tests...${NC}"
        pytest CI/tests/test_e2e.py -m e2e -v --tb=short --cov=src --cov=containers --cov-config=CI/config/.coveragerc -c CI/config/pytest.ini
        ;;
    all)
        echo -e "${GREEN}Running all tests...${NC}"
        pytest CI/tests/ \
            --cov=src \
            --cov=containers \
            --cov-config=CI/config/.coveragerc \
            --cov-report=term-missing \
            --cov-report=html:CI/coverage_html \
            --cov-fail-under=60 \
            -c CI/config/pytest.ini \
            -v
        ;;
    *)
        echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
        echo "Usage: $0 [unit|integration|e2e|all]"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Tests completed!${NC}"

