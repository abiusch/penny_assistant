#!/usr/bin/env python3
"""
Quick test to verify health monitor integration works
"""

import sys
import os

# Add src directory to Python path  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from memory_enhanced_pipeline import MemoryEnhancedPipeline
import asyncio

async def test_health_monitor():
    """Test that health monitor integration doesn't crash."""
    print("🧪 Testing health monitor integration...")
    
    try:
        # Initialize pipeline (should not crash)
        pipeline = MemoryEnhancedPipeline()
        print("✅ Pipeline initialization successful")
        
        # Test health check (should not crash)  
        health_stats = await pipeline.health_monitor.check_all_components()
        print("✅ Health check completed")
        print(f"📊 Health stats: {health_stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_health_monitor())
    if success:
        print("\n🎉 Health monitor fix is working!")
    else:
        print("\n💥 Health monitor still has issues")
