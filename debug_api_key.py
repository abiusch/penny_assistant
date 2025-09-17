#!/usr/bin/env python3
"""
Debug API Key Issues
Check where the ELEVENLABS_API_KEY is and why it keeps disappearing
"""

import os
import subprocess

def check_api_key_status():
    print("🔍 Debugging ELEVENLABS_API_KEY Issues")
    print("="*50)
    
    # Check current environment
    print("1. Current Environment Variable:")
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if api_key:
        print(f"   ✅ ELEVENLABS_API_KEY is set: {api_key[:10]}...{api_key[-4:]}")
    else:
        print("   ❌ ELEVENLABS_API_KEY is not set in current environment")
    
    # Check if it's in the shell environment
    print("\n2. Shell Environment Check:")
    try:
        result = subprocess.run(['printenv', 'ELEVENLABS_API_KEY'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            shell_key = result.stdout.strip()
            print(f"   ✅ Found in shell: {shell_key[:10]}...{shell_key[-4:]}")
        else:
            print("   ❌ Not found in shell environment")
    except Exception as e:
        print(f"   ⚠️ Could not check shell: {e}")
    
    # Check common shell profile files
    print("\n3. Shell Profile Files:")
    profile_files = [
        "~/.zshrc",
        "~/.bash_profile", 
        "~/.bashrc",
        "~/.profile"
    ]
    
    for profile in profile_files:
        expanded_path = os.path.expanduser(profile)
        if os.path.exists(expanded_path):
            print(f"   📄 {profile} exists")
            try:
                with open(expanded_path, 'r') as f:
                    content = f.read()
                    if "ELEVENLABS_API_KEY" in content:
                        print(f"   ✅ {profile} contains ELEVENLABS_API_KEY")
                        # Find the line
                        lines = content.split('\n')
                        for line in lines:
                            if "ELEVENLABS_API_KEY" in line and not line.strip().startswith('#'):
                                print(f"      Line: {line.strip()}")
                    else:
                        print(f"   ❌ {profile} does not contain ELEVENLABS_API_KEY")
            except Exception as e:
                print(f"   ⚠️ Could not read {profile}: {e}")
        else:
            print(f"   ❌ {profile} does not exist")
    
    # Check current shell
    print(f"\n4. Current Shell:")
    current_shell = os.getenv("SHELL", "unknown")
    print(f"   Shell: {current_shell}")
    
    # Check if we're in the right directory for .env files
    print(f"\n5. Current Directory & Config Files:")
    current_dir = os.getcwd()
    print(f"   Current directory: {current_dir}")
    
    config_files = [
        "penny_config.json",
        ".env",
        ".env.local"
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"   📄 {config_file} exists")
            if config_file.endswith('.env') or config_file.endswith('.env.local'):
                try:
                    with open(config_file, 'r') as f:
                        content = f.read()
                        if "ELEVENLABS_API_KEY" in content:
                            print(f"   ✅ {config_file} contains ELEVENLABS_API_KEY")
                        else:
                            print(f"   ❌ {config_file} does not contain ELEVENLABS_API_KEY")
                except Exception as e:
                    print(f"   ⚠️ Could not read {config_file}: {e}")
        else:
            print(f"   ❌ {config_file} does not exist")

def suggest_fixes():
    print(f"\n💡 Suggested Fixes:")
    print("="*30)
    
    current_shell = os.getenv("SHELL", "")
    
    if "zsh" in current_shell:
        profile_file = "~/.zshrc"
    elif "bash" in current_shell:
        profile_file = "~/.bash_profile"
    else:
        profile_file = "~/.profile"
    
    print(f"1. Add to {profile_file} (permanent):")
    print(f"   echo 'export ELEVENLABS_API_KEY=\"your-api-key-here\"' >> {profile_file}")
    print(f"   source {profile_file}")
    
    print(f"\n2. Set for current session:")
    print(f"   export ELEVENLABS_API_KEY=\"your-api-key-here\"")
    
    print(f"\n3. Create .env file in project directory:")
    print(f"   echo 'ELEVENLABS_API_KEY=your-api-key-here' > .env")
    print(f"   (Then update code to load .env file)")
    
    print(f"\n4. Test if it's working:")
    print(f"   echo $ELEVENLABS_API_KEY")
    print(f"   python3 -c \"import os; print('API Key:', os.getenv('ELEVENLABS_API_KEY'))\"")

if __name__ == "__main__":
    check_api_key_status()
    suggest_fixes()
