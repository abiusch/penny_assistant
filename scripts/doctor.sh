#!/bin/bash

# Penny Doctor - Shell Wrapper
# Provides easy access to PennyGPT system health checks

cd "$(dirname "$0")/.."

echo "🏥 Starting Penny Doctor..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    echo "Install Python 3.9+ and try again."
    exit 1
fi

# Set PYTHONPATH for imports
export PYTHONPATH="$PWD/src:$PYTHONPATH"

# Run the doctor
python3 penny_doctor.py "$@"

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo "🎉 All systems go! Your PennyGPT is healthy."
else
    echo "⚠️  Issues found. Check the output above for fixes."
fi

exit $exit_code
