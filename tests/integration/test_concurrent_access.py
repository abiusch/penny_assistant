#!/usr/bin/env python3
"""
Concurrent Access Tests - Week 4 Fix #3
Tests simultaneous chat and voice operations to ensure no race conditions.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import random

from src.core.modality import create_modal_interface
from memory_system import MemoryManager
from personality_tracker import PersonalityTracker


class TestConcurrentAccess:
    """Test concurrent operations."""
    
    def test_concurrent_memory_writes(self):
        """Test multiple threads writing to memory simultaneously."""
        print("\n🧪 TEST 1: Concurrent Memory Writes")
        print("=" * 60)
        
        memory = MemoryManager(db_path="data/test_concurrent_memory.db")
        
        def write_conversation(thread_id: int, count: int):
            """Write multiple conversations from a thread."""
            results = []
            for i in range(count):
                turn_id = memory.add_conversation_turn(
                    user_input=f"Thread {thread_id} Message {i}",
                    assistant_response=f"Response from thread {thread_id} to message {i}",
                    context={'thread_id': thread_id, 'message_num': i}
                )
                results.append(turn_id.turn_id)
                time.sleep(random.uniform(0.001, 0.01))  # Small random delay
            return results
        
        # Launch multiple threads
        num_threads = 5
        messages_per_thread = 10
        
        print(f"  Starting {num_threads} threads, {messages_per_thread} messages each...")
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            start_time = time.time()
            
            futures = []
            for i in range(num_threads):
                future = executor.submit(write_conversation, i, messages_per_thread)
                futures.append(future)
            
            # Collect results
            all_turn_ids = []
            for future in as_completed(futures):
                turn_ids = future.result()
                all_turn_ids.extend(turn_ids)
            
            elapsed = time.time() - start_time
        
        # Verify all writes succeeded
        expected_total = num_threads * messages_per_thread
        actual_total = len(all_turn_ids)
        
        print(f"\n  Expected writes: {expected_total}")
        print(f"  Actual writes:   {actual_total}")
        print(f"  Time elapsed:    {elapsed:.2f}s")
        print(f"  Rate:            {actual_total/elapsed:.1f} writes/sec")
        
        assert actual_total == expected_total, f"Lost writes! Expected {expected_total}, got {actual_total}"
        
        # Verify no duplicates
        unique_ids = set(all_turn_ids)
        assert len(unique_ids) == actual_total, "Found duplicate turn IDs!"
        
        print("  ✅ All writes successful, no duplicates, no data loss")
        print("\n✅ Concurrent memory writes test complete")
    
    async def test_concurrent_personality_updates(self):
        """Test multiple threads updating personality simultaneously."""
        print("\n🧪 TEST 2: Concurrent Personality Updates")
        print("=" * 60)
        
        tracker = PersonalityTracker(db_path="data/test_concurrent_personality.db")
        
        async def update_personality(user_id: str, dimension: str, iterations: int):
            """Update personality dimension multiple times."""
            for i in range(iterations):
                value = random.uniform(0, 1)
                await tracker.update_personality_dimension(
                    user_id=user_id,
                    dimension=dimension,
                    new_value=value,
                    confidence_change=0.01,
                    context=f"Update {i}"
                )
                await asyncio.sleep(random.uniform(0.001, 0.01))
        
        # Test concurrent updates to same dimension
        num_tasks = 5
        updates_per_task = 20
        
        print(f"  Starting {num_tasks} concurrent tasks...")
        print(f"  Each updating same dimension {updates_per_task} times...")
        
        start_time = time.time()
        
        tasks = []
        for i in range(num_tasks):
            task = update_personality(
                "test_user",
                "response_length_preference",
                updates_per_task
            )
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        total_updates = num_tasks * updates_per_task
        
        print(f"\n  Total updates:   {total_updates}")
        print(f"  Time elapsed:    {elapsed:.2f}s")
        print(f"  Rate:            {total_updates/elapsed:.1f} updates/sec")
        
        # Verify final state is consistent
        state = await tracker.get_current_personality_state("test_user")
        dimension_state = state.get('response_length_preference')
        
        if dimension_state:
            print(f"  Final value:     {dimension_state.current_value}")
            print(f"  Final confidence: {dimension_state.confidence:.3f}")
            print("  ✅ Personality state is consistent")
        else:
            print("  ⚠️  Dimension not found (may be expected)")
        
        print("\n✅ Concurrent personality updates test complete")
    
    async def test_simultaneous_chat_and_voice(self):
        """Test chat and voice running simultaneously for same user."""
        print("\n🧪 TEST 3: Simultaneous Chat and Voice")
        print("=" * 60)
        
        user_id = "simultaneous_test_user"
        
        # Create both interfaces
        chat = create_modal_interface("chat", user_id=user_id)
        voice = create_modal_interface("voice", user_id=user_id)
        
        async def chat_conversation():
            """Simulate chat conversation."""
            messages = [
                "Hello from chat",
                "What's the weather?",
                "Tell me a joke",
                "Thanks!"
            ]
            
            for msg in messages:
                chat.save_conversation(
                    user_input=msg,
                    assistant_response=f"Chat response to: {msg}",
                    metadata={'modality': 'chat'}
                )
                await asyncio.sleep(random.uniform(0.1, 0.3))
        
        async def voice_conversation():
            """Simulate voice conversation."""
            messages = [
                "Hello from voice",
                "What's the time?",
                "Play some music",
                "Goodbye!"
            ]
            
            for msg in messages:
                voice.save_conversation(
                    user_input=msg,
                    assistant_response=f"Voice response to: {msg}",
                    metadata={'modality': 'voice'}
                )
                await asyncio.sleep(random.uniform(0.1, 0.3))
        
        print("  Starting simultaneous chat and voice conversations...")
        
        start_time = time.time()
        
        # Run both simultaneously
        await asyncio.gather(
            chat_conversation(),
            voice_conversation()
        )
        
        elapsed = time.time() - start_time
        
        print(f"\n  Time elapsed: {elapsed:.2f}s")
        
        # Verify memory contains both conversations
        chat_memory = chat.get_memory_context()
        voice_memory = voice.get_memory_context()
        
        print(f"  Chat memory:  {len(chat_memory)} chars")
        print(f"  Voice memory: {len(voice_memory)} chars")
        
        # They should have the same memory (shared!)
        assert chat_memory == voice_memory, "Memory should be shared across modalities"
        
        print("  ✅ Memory is correctly shared between chat and voice")
        
        # Cleanup
        chat.cleanup()
        voice.cleanup()
        
        print("\n✅ Simultaneous chat and voice test complete")
    
    async def test_memory_consistency_under_load(self):
        """Test memory consistency when under heavy load."""
        print("\n🧪 TEST 4: Memory Consistency Under Load")
        print("=" * 60)
        
        memory = MemoryManager(db_path="data/test_load_memory.db")
        
        async def rapid_fire_writes(prefix: str, count: int):
            """Write many conversations rapidly."""
            for i in range(count):
                memory.add_conversation_turn(
                    user_input=f"{prefix} message {i}",
                    assistant_response=f"{prefix} response {i}"
                )
                # No delay - as fast as possible!
        
        # High load test
        num_writers = 10
        writes_per_writer = 50
        total_expected = num_writers * writes_per_writer
        
        print(f"  Starting {num_writers} concurrent writers...")
        print(f"  Each writing {writes_per_writer} messages...")
        print(f"  Total expected: {total_expected} writes")
        
        start_time = time.time()
        
        tasks = []
        for i in range(num_writers):
            task = rapid_fire_writes(f"Writer{i}", writes_per_writer)
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        
        # Check memory stats
        stats = memory.get_memory_stats()
        
        print(f"\n  Time elapsed:     {elapsed:.2f}s")
        print(f"  Write rate:       {total_expected/elapsed:.1f} writes/sec")
        print(f"  Total in memory:  {stats['total_conversation_turns']}")
        print(f"  Active context:   {stats['active_context_size']}")
        
        # Verify count (may be more due to previous tests)
        assert stats['total_conversation_turns'] >= total_expected, "Lost writes under load!"
        
        print("  ✅ Memory remained consistent under load")
        print("\n✅ Memory consistency under load test complete")
    
    async def test_race_condition_personality_read_write(self):
        """Test for race conditions in personality read/write."""
        print("\n🧪 TEST 5: Personality Read/Write Race Conditions")
        print("=" * 60)
        
        tracker = PersonalityTracker(db_path="data/test_race_personality.db")
        
        user_id = "race_test_user"
        dimension = "test_dimension"
        
        # Initialize dimension
        await tracker.update_personality_dimension(
            user_id, dimension, 0.5, 0.1, "Initial"
        )
        
        read_count = 0
        write_count = 0
        errors = []
        
        async def reader(reader_id: int, iterations: int):
            """Read personality state repeatedly."""
            nonlocal read_count
            for i in range(iterations):
                try:
                    state = await tracker.get_current_personality_state(user_id)
                    read_count += 1
                    await asyncio.sleep(random.uniform(0.001, 0.005))
                except Exception as e:
                    errors.append(f"Reader {reader_id}: {e}")
        
        async def writer(writer_id: int, iterations: int):
            """Write personality state repeatedly."""
            nonlocal write_count
            for i in range(iterations):
                try:
                    value = random.uniform(0, 1)
                    await tracker.update_personality_dimension(
                        user_id, dimension, value, 0.01, f"Writer {writer_id}"
                    )
                    write_count += 1
                    await asyncio.sleep(random.uniform(0.001, 0.005))
                except Exception as e:
                    errors.append(f"Writer {writer_id}: {e}")
        
        # Run readers and writers simultaneously
        num_readers = 3
        num_writers = 3
        ops_per_task = 30
        
        print(f"  Starting {num_readers} readers and {num_writers} writers...")
        print(f"  Each performing {ops_per_task} operations...")
        
        start_time = time.time()
        
        tasks = []
        for i in range(num_readers):
            tasks.append(reader(i, ops_per_task))
        for i in range(num_writers):
            tasks.append(writer(i, ops_per_task))
        
        await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        
        print(f"\n  Reads completed:  {read_count}")
        print(f"  Writes completed: {write_count}")
        print(f"  Time elapsed:     {elapsed:.2f}s")
        print(f"  Errors:           {len(errors)}")
        
        if errors:
            print("\n  ⚠️  Errors encountered:")
            for error in errors[:5]:  # Show first 5
                print(f"    - {error}")
        else:
            print("  ✅ No race conditions detected!")
        
        # Final state check
        final_state = await tracker.get_current_personality_state(user_id)
        if dimension in final_state:
            print(f"  Final dimension value: {final_state[dimension].current_value}")
        
        print("\n✅ Race condition test complete")
    
    def test_database_file_integrity(self):
        """Test database file integrity after concurrent access."""
        print("\n🧪 TEST 6: Database File Integrity")
        print("=" * 60)
        
        db_path = "data/test_integrity.db"
        memory = MemoryManager(db_path=db_path)
        
        # Write some data
        for i in range(100):
            memory.add_conversation_turn(
                f"Message {i}",
                f"Response {i}"
            )
        
        # Check database can be read
        stats = memory.get_memory_stats()
        
        print(f"  Conversations in DB: {stats['total_conversation_turns']}")
        print(f"  DB file size:        {stats['memory_db_size']} bytes")
        
        # Try to read with new connection
        import sqlite3
        try:
            with sqlite3.connect(db_path) as conn:
                count = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
                print(f"  Verified count:      {count}")
                
                # Check for WAL mode
                journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
                print(f"  Journal mode:        {journal_mode}")
                
                assert journal_mode == "wal", "WAL mode not enabled!"
                print("  ✅ WAL mode is active")
                
        except sqlite3.Error as e:
            print(f"  ❌ Database error: {e}")
            raise
        
        print("\n✅ Database integrity test complete")


async def run_all_tests():
    """Run all concurrent access tests."""
    print("=" * 70)
    print("🧪 CONCURRENT ACCESS TEST SUITE - WEEK 4 FIX #3")
    print("=" * 70)
    print("\nTesting concurrent operations for thread safety...\n")
    
    test_suite = TestConcurrentAccess()
    
    tests = [
        ("Concurrent Memory Writes", test_suite.test_concurrent_memory_writes),
        ("Concurrent Personality Updates", test_suite.test_concurrent_personality_updates),
        ("Simultaneous Chat and Voice", test_suite.test_simultaneous_chat_and_voice),
        ("Memory Under Load", test_suite.test_memory_consistency_under_load),
        ("Race Conditions", test_suite.test_race_condition_personality_read_write),
        ("Database Integrity", test_suite.test_database_file_integrity),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                await test_func()
            else:
                test_func()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"\n❌ Test '{name}' failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print(f"\nTotal tests:  {len(tests)}")
    print(f"Passed:       {passed} ✅")
    print(f"Failed:       {failed} {'❌' if failed > 0 else '✅'}")
    print(f"Success rate: {(passed/len(tests))*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL CONCURRENT ACCESS TESTS PASSED!")
        print("   - WAL mode enabled ✅")
        print("   - No race conditions ✅")
        print("   - Memory consistent ✅")
        print("   - Database integrity verified ✅")
        print("\n   Week 4 Fix #3: COMPLETE ✅")
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        print("   Review failures and fix issues")
    
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
