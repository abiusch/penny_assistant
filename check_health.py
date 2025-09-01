#!/usr/bin/env python3
"""
Quick health check script for PennyGPT
Usage: python check_health.py
"""

import sys
import os
import asyncio

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from health_monitor import PennyGPTHealthMonitor


async def main():
    """Quick health check entry point."""
    print("🏥 PennyGPT Health Check")
    print("=" * 30)
    
    try:
        monitor = PennyGPTHealthMonitor()
        is_healthy = await monitor.run_health_check()
        
        if is_healthy:
            print("\n🎉 System is ready!")
            return 0
        else:
            print("\n⚠️  Please resolve issues before running PennyGPT.")
            return 1
            
    except FileNotFoundError as e:
        if "penny_config.json" in str(e):
            print("❌ Configuration file 'penny_config.json' not found.")
            print("💡 Please ensure you're running from the project root directory.")
        else:
            print(f"❌ File not found: {e}")
        return 1
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return 1
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
