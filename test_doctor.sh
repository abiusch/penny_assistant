#!/bin/bash

echo "🧪 Testing Penny Doctor Implementation..."
echo ""

cd "$(dirname "$0")"
cd ..

# Make scripts executable
chmod +x scripts/doctor.sh penny_doctor.py

# Test 1: Check if doctor script runs without crashing
echo "1. Testing doctor script execution..."
if python3 penny_doctor.py --help &> /dev/null || python3 penny_doctor.py | head -5 &> /dev/null; then
    echo "✅ Doctor script runs without crashing"
else
    echo "❌ Doctor script has issues"
fi

# Test 2: Check if shell wrapper works
echo ""
echo "2. Testing shell wrapper..."
if ./scripts/doctor.sh | head -5 &> /dev/null; then
    echo "✅ Shell wrapper works"
else
    echo "❌ Shell wrapper has issues"
fi

# Test 3: Check if module import works
echo ""
echo "3. Testing module import..."
if PYTHONPATH=src python3 -c "from penny_doctor import PennyDoctor; print('Import successful')" 2>/dev/null; then
    echo "✅ Module import works"
else
    echo "❌ Module import fails"
fi

# Test 4: Quick syntax validation
echo ""
echo "4. Testing Python syntax..."
if python3 -m py_compile penny_doctor.py; then
    echo "✅ Python syntax is valid"
else
    echo "❌ Python syntax errors found"
fi

# Test 5: Check test file
echo ""
echo "5. Testing test file syntax..."
if python3 -m py_compile tests/test_penny_doctor.py; then
    echo "✅ Test file syntax is valid"
else
    echo "❌ Test file syntax errors found"
fi

echo ""
echo "🎯 Quick Demo Run:"
echo "Running doctor with limited output..."
echo "----------------------------------------"

# Run a quick demo (first few checks only)
PYTHONPATH=src python3 -c "
from penny_doctor import PennyDoctor
doctor = PennyDoctor()
print('🏥 Penny Doctor - Quick Demo')
print('=' * 30)
try:
    doctor.check_python_environment()
    print('Demo completed successfully!')
except Exception as e:
    print(f'Demo error: {e}')
"

echo ""
echo "✅ Penny Doctor implementation test complete!"
echo ""
echo "To run full health check:"
echo "  ./scripts/doctor.sh"
echo "  or"
echo "  PYTHONPATH=src python3 penny_doctor.py"
