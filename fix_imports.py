#!/usr/bin/env python3
"""Fix all imports to remove 'src.' prefix since we're using PYTHONPATH=src"""

import os
import re

def fix_imports_in_file(filepath):
    """Fix imports in a single file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Replace all "from src." with "from "
    original = content
    content = re.sub(r'from src\.', 'from ', content)
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed: {filepath}")
        return True
    return False

def main():
    """Fix all Python files in src/ directory."""
    fixed_count = 0
    
    # Walk through src/ directory
    for root, dirs, files in os.walk('src/'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if fix_imports_in_file(filepath):
                    fixed_count += 1
    
    print(f"\nFixed {fixed_count} files")
    print("\nNow run: PYTHONPATH=src pytest -q tests --ignore=whisper --tb=short")

if __name__ == "__main__":
    main()
