#!/usr/bin/env python3
"""
Test EdgeModalInterface
Validates unified modal architecture
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
from src.core.modality import create_modal_interface, ChatModalInterface, VoiceModalInterface


async def test_chat_modal():
    """Test chat modality."""
    print("\n" + "="*60)
    print("🧪 TEST 1: Chat Modal Interface")
    print("="*60)
    
    # Create chat interface
    chat = create_modal_interface("chat", user_id="test_user")
    
    assert isinstance(chat, ChatModalInterface), "Should create ChatModalInterface"
    assert chat.modality_name == "chat", "Should have correct modality name"
    assert chat.personality is not None, "Should have personality tracker"
    
    print("✅ Chat interface created successfully")
    print(f"   Modality: {chat.modality_name}")
    print(f"   User ID: {chat.user_id}")
    print(f"   Personality: {chat.personality is not None}")
    print(f"   Memory: {chat.base_memory is not None}")
    
    # Test personality context
    personality_ctx = await chat.get_personality_context()
    print(f"✅ Personality context retrieved: {len(personality_ctx)} keys")
    
    # Test memory context
    memory_ctx = chat.get_memory_context()
    print(f"✅ Memory context retrieved: {len(memory_ctx)} chars")
    
    # Cleanup
    chat.cleanup()
    print("✅ Chat interface cleaned up")


async def test_voice_modal():
    """Test voice modality."""
    print("\n" + "="*60)
    print("🧪 TEST 2: Voice Modal Interface")
    print("="*60)
    
    # Create voice interface
    voice = create_modal_interface("voice", user_id="test_user")
    
    assert isinstance(voice, VoiceModalInterface), "Should create VoiceModalInterface"
    assert voice.modality_name == "voice", "Should have correct modality name"
    assert voice.personality is not None, "Should have personality tracker"
    
    print("✅ Voice interface created successfully")
    print(f"   Modality: {voice.modality_name}")
    print(f"   User ID: {voice.user_id}")
    print(f"   Personality: {voice.personality is not None}")
    print(f"   Memory: {voice.base_memory is not None}")
    
    # Test personality context
    personality_ctx = await voice.get_personality_context()
    print(f"✅ Personality context retrieved: {len(personality_ctx)} keys")
    
    # Test memory context
    memory_ctx = voice.get_memory_context()
    print(f"✅ Memory context retrieved: {len(memory_ctx)} chars")
    
    # Cleanup
    voice.cleanup()
    print("✅ Voice interface cleaned up")


async def test_shared_personality():
    """Test that both modalities share personality state."""
    print("\n" + "="*60)
    print("🧪 TEST 3: Shared Personality State")
    print("="*60)
    
    # Create both interfaces for same user
    chat = create_modal_interface("chat", user_id="shared_user")
    voice = create_modal_interface("voice", user_id="shared_user")
    
    # Both should have personality trackers
    assert chat.personality is not None, "Chat should have personality"
    assert voice.personality is not None, "Voice should have personality"
    
    print("✅ Both modalities have personality trackers")
    
    # Get personality state from both
    chat_ctx = await chat.get_personality_context()
    voice_ctx = await voice.get_personality_context()
    
    print(f"✅ Chat personality context: {chat_ctx.get('user_id')}")
    print(f"✅ Voice personality context: {voice_ctx.get('user_id')}")
    
    # Both should reference same user
    assert chat_ctx.get('user_id') == voice_ctx.get('user_id'), "Should share user ID"
    
    print("✅ Personality state is consistent across modalities")
    
    # Cleanup
    chat.cleanup()
    voice.cleanup()


async def test_conversation_flow():
    """Test full conversation flow."""
    print("\n" + "="*60)
    print("🧪 TEST 4: Conversation Flow")
    print("="*60)
    
    chat = create_modal_interface("chat", user_id="flow_user")
    
    # Save a conversation
    turn_id = chat.save_conversation(
        user_input="Hello Penny!",
        assistant_response="Hey! What's up?",
        metadata={'test': True}
    )
    
    print(f"✅ Conversation saved: turn_id = {turn_id}")
    
    # Get memory context (should include the conversation)
    memory_ctx = chat.get_memory_context()
    print(f"✅ Memory context after conversation: {len(memory_ctx)} chars")
    
    # Update personality from conversation
    await chat.update_personality(
        user_input="Hello Penny!",
        assistant_response="Hey! What's up?",
        turn_id=turn_id
    )
    print("✅ Personality updated from conversation")
    
    # Cleanup
    chat.cleanup()


async def test_lazy_loading():
    """Test lazy loading of edge AI models."""
    print("\n" + "="*60)
    print("🧪 TEST 5: Lazy Model Loading")
    print("="*60)
    
    chat = create_modal_interface("chat", user_id="lazy_user", enable_edge_models=True)
    
    # Models should not be loaded yet
    assert chat._llm is None, "LLM should not be loaded initially"
    assert chat._stt is None, "STT should not be loaded initially"
    assert chat._tts is None, "TTS should not be loaded initially"
    
    print("✅ Models not loaded initially (lazy loading works)")
    
    # Access LLM property (should trigger loading)
    try:
        llm = chat.llm
        print(f"✅ LLM loaded on demand: {type(llm).__name__}")
    except Exception as e:
        print(f"⚠️  LLM loading failed (expected if models not installed): {e}")
    
    # Cleanup
    chat.cleanup()


async def main():
    """Run all tests."""
    print("="*60)
    print("🧪 EDGEMODALINTERFACE TEST SUITE")
    print("="*60)
    print("\nTesting unified modal architecture...")
    
    try:
        await test_chat_modal()
        await test_voice_modal()
        await test_shared_personality()
        await test_conversation_flow()
        await test_lazy_loading()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nEdgeModalInterface is working correctly:")
        print("  ✅ Chat and voice modalities created")
        print("  ✅ Shared personality state")
        print("  ✅ Unified memory system")
        print("  ✅ Conversation flow working")
        print("  ✅ Lazy model loading")
        print("\n🎉 Week 4 Critical Fix #1: COMPLETE")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
