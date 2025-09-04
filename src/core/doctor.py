"""
Core Doctor Module - PennyGPT System Health Checker
Can be run as: python -m core.doctor
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from penny_doctor import main

if __name__ == "__main__":
    main()
