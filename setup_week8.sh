#!/bin/bash
# Week 8 Setup Script
# Installs dependencies needed for emotional continuity

echo "=========================================="
echo "Week 8 Emotional Continuity Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

# Install transformers for emotion detection
echo ""
echo "Installing transformers library (for emotion detection)..."
pip install --break-system-packages transformers torch --quiet

# Install pytest if not present
echo ""
echo "Installing pytest (for testing)..."
pip install --break-system-packages pytest --quiet

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Run validation: python validate_week8.py"
echo "2. If all tests pass, proceed with integration"
echo ""
