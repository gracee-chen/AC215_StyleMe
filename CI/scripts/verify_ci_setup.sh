#!/bin/bash
# Quick verification script to check if CI setup is correct

echo "🔍 Verifying CI Setup..."
echo "========================="
echo ""

# Check if we're in the right directory
if [ ! -f "CI/README.md" ]; then
    echo "❌ Error: Run this script from project root"
    exit 1
fi

echo "✅ Project root found"
echo ""

# Check CI files
echo "📁 Checking CI files..."
FILES=(
    ".github/workflows/ci.yml"
    "CI/config/.flake8"
    "CI/config/.coveragerc"
    "CI/config/pytest.ini"
    "CI/requirements-dev.txt"
    "CI/tests/test_inference.py"
    "CI/tests/integration/test_pipeline.py"
    "CI/tests/test_e2e.py"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (MISSING)"
    fi
done

echo ""

# Check Python
echo "🐍 Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "  ✅ Python: $PYTHON_VERSION"
else
    echo "  ❌ Python 3 not found"
fi

echo ""

# Check if pytest is available
echo "🧪 Checking test tools..."
if command -v pytest &> /dev/null; then
    echo "  ✅ pytest installed"
else
    echo "  ⚠️  pytest not installed (run: ./CI/scripts/setup_ci_env.sh)"
fi

if command -v flake8 &> /dev/null; then
    echo "  ✅ flake8 installed"
else
    echo "  ⚠️  flake8 not installed (run: ./CI/scripts/setup_ci_env.sh)"
fi

echo ""

# Check git
echo "📦 Checking Git..."
if command -v git &> /dev/null; then
    if git remote -v &> /dev/null; then
        echo "  ✅ Git repository configured"
        echo "  📍 Remote: $(git remote get-url origin 2>/dev/null | head -1)"
        echo "  🌿 Branch: $(git branch --show-current 2>/dev/null)"
    else
        echo "  ⚠️  Git repository but no remote configured"
    fi
else
    echo "  ❌ Git not found"
fi

echo ""
echo "========================="
echo "✅ CI Setup Verification Complete!"
echo ""
echo "Next steps:"
echo "  1. Run: ./CI/scripts/setup_ci_env.sh"
echo "  2. Run: ./CI/scripts/run_lint.sh"
echo "  3. Run: ./CI/scripts/run_tests.sh"
echo "  4. Commit and push to trigger GitHub Actions CI"
echo ""

