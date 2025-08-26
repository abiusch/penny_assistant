#!/usr/bin/env python3
"""Script to consolidate package layout to src/ only."""

import os
import shutil
import glob

def move_to_src():
    """Move top-level core/ and adapters/ to src/"""
    
    # Create src directories if they don't exist
    os.makedirs("src/core", exist_ok=True)
    os.makedirs("src/adapters", exist_ok=True)
    
    # Move core/ contents to src/core/
    if os.path.exists("core"):
        print("Moving core/ to src/core/...")
        for item in os.listdir("core"):
            src_path = os.path.join("core", item)
            dst_path = os.path.join("src/core", item)
            
            if os.path.exists(dst_path):
                print(f"  Skipping {item} (already exists in src/core/)")
                continue
                
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)
            print(f"  Moved {item}")
    
    # Move adapters/ contents to src/adapters/
    if os.path.exists("adapters"):
        print("Moving adapters/ to src/adapters/...")
        for item in os.listdir("adapters"):
            src_path = os.path.join("adapters", item)
            dst_path = os.path.join("src/adapters", item)
            
            if os.path.exists(dst_path):
                print(f"  Skipping {item} (already exists in src/adapters/)")
                continue
                
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)
            print(f"  Moved {item}")

def update_imports():
    """Update import statements in Python files."""
    
    # Find all Python files
    python_files = []
    for pattern in ["*.py", "**/*.py"]:
        python_files.extend(glob.glob(pattern, recursive=True))
    
    # Exclude files in directories we don't want to modify
    exclude_dirs = ["__pycache__", ".git", "venv", ".venv", "bin", "PennyGPT-Project"]
    python_files = [f for f in python_files if not any(exc in f for exc in exclude_dirs)]
    
    print(f"\nUpdating imports in {len(python_files)} Python files...")
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Update imports
            # from core.xxx -> from src.core.xxx
            content = content.replace("from core.", "from src.core.")
            content = content.replace("import core.", "import src.core.")
            
            # from adapters.xxx -> from src.adapters.xxx  
            content = content.replace("from adapters.", "from src.adapters.")
            content = content.replace("import adapters.", "import src.adapters.")
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  Updated imports in {file_path}")
                
        except Exception as e:
            print(f"  Error updating {file_path}: {e}")

def cleanup_old_dirs():
    """Remove old top-level directories after successful move."""
    print("\nCleaning up old directories...")
    
    if os.path.exists("core"):
        shutil.rmtree("core")
        print("  Removed top-level core/")
    
    if os.path.exists("adapters"):
        shutil.rmtree("adapters")
        print("  Removed top-level adapters/")

if __name__ == "__main__":
    print("🔧 Consolidating package layout to src/ only...")
    
    move_to_src()
    update_imports()
    cleanup_old_dirs()
    
    print("\n✅ Package layout consolidation complete!")
    print("All code is now under src/ directory with updated imports.")
