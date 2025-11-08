#!/bin/bash
# Quick demo script for Emergency Building Sweep Simulator

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Emergency Building Sweep Simulator - Quick Demo         ║"
echo "║  HiMCM 2025 MVP                                           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found. Please install Python 3.11+"
    exit 1
fi

echo "✓ Python 3 found"
echo ""

# Check dependencies
echo "Checking dependencies..."
python3 -c "import numpy, matplotlib, pandas, networkx" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Some dependencies missing. Installing..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
fi
echo "✓ All dependencies installed"
echo ""

# Run tests
echo "Running acceptance tests..."
python3 test_acceptance.py
if [ $? -ne 0 ]; then
    echo "❌ Tests failed"
    exit 1
fi
echo ""

# Run demo
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Running Demo Simulation                                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Scenario: Simple office (1 floor, 1 agent, no hazards)"
echo "Running in headless mode for speed..."
echo ""

python3 main.py --no-viz --scenario simple

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Demo Complete!                                           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. View results in the outputs/ directory"
echo "  2. Run with visualization: python3 main.py"
echo "  3. Try other scenarios: python3 main.py --scenario office"
echo "  4. See USAGE.md for more options"
echo ""
echo "Enjoy! 🚒"

