#!/usr/bin/env python3
"""Final cleanup script to remove empty old directories."""

import os
import shutil

def remove_empty_dirs():
    """Remove empty old directories."""
    dirs_to_remove = [
        "core/stt",
        "core/tts", 
        "core/vad",
        "core/testing",
        "core",
        "adapters/llm",
        "adapters/stt",
        "adapters/tts", 
        "adapters/vad",
        "adapters"
    ]
    
    for dir_path in dirs_to_remove:
        if os.path.exists(dir_path):
            try:
                if os.path.isdir(dir_path):
                    # Check if directory is empty
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
                        print(f"✅ Removed empty directory: {dir_path}")
                    else:
                        print(f"⚠️  Directory not empty: {dir_path}")
                        # List contents
                        contents = os.listdir(dir_path)
                        print(f"   Contents: {contents}")
                else:
                    print(f"⚠️  Not a directory: {dir_path}")
            except Exception as e:
                print(f"❌ Error removing {dir_path}: {e}")

if __name__ == "__main__":
    print("🧹 Final cleanup: removing empty old directories...")
    remove_empty_dirs()
    print("✅ Cleanup complete!")
