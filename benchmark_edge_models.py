#!/usr/bin/env python3
"""
Benchmark Edge AI Stack
Tests performance of all local models for Penny
"""

import subprocess
import time
import json
import os
import sys

def benchmark_ollama(model_name, prompt):
    """Benchmark Ollama model"""
    print(f"\n🧠 Benchmarking {model_name}...")
    print(f"   Prompt: '{prompt}'")
    
    try:
        start = time.time()
        result = subprocess.run(
            ["ollama", "run", model_name, prompt],
            capture_output=True,
            text=True,
            timeout=30
        )
        latency = time.time() - start
        
        if result.returncode == 0:
            print(f"   ✅ Latency: {latency:.2f}s")
            print(f"   Output: {result.stdout[:100].strip()}...")
            return latency
        else:
            print(f"   ❌ Failed: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print(f"   ❌ Timeout (>30s)")
        return None
    except FileNotFoundError:
        print(f"   ❌ Ollama not installed")
        return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def benchmark_whisper():
    """Benchmark Whisper.cpp"""
    print(f"\n🎤 Benchmarking Whisper.cpp...")

    whisper_path = "whisper.cpp/build/bin/whisper-cli"
    model_path = "whisper.cpp/models/ggml-large-v3.bin"
    audio_path = "whisper.cpp/samples/jfk.wav"
    
    if not os.path.exists(whisper_path):
        print(f"   ❌ Whisper not installed at {whisper_path}")
        return None
    
    if not os.path.exists(model_path):
        print(f"   ❌ Model not found at {model_path}")
        return None
    
    if not os.path.exists(audio_path):
        print(f"   ❌ Sample audio not found at {audio_path}")
        return None
    
    try:
        start = time.time()
        result = subprocess.run(
            [whisper_path, "-m", model_path, "-f", audio_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        latency = time.time() - start
        
        if result.returncode == 0:
            print(f"   ✅ Latency: {latency:.2f}s")
            # Extract transcription
            lines = result.stdout.split('\n')
            transcription = [l for l in lines if l.strip() and not l.startswith('[')]
            if transcription:
                print(f"   Output: {transcription[0][:100]}...")
            return latency
        else:
            print(f"   ❌ Failed: {result.stderr[:200]}")
            return None
            
    except subprocess.TimeoutExpired:
        print(f"   ❌ Timeout (>30s)")
        return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def benchmark_tts():
    """Benchmark Piper TTS"""
    print(f"\n🔊 Benchmarking Piper TTS...")

    test_file = "benchmark_tts_test.wav"
    model_path = "piper_models/en_US-lessac-medium.onnx"

    if not os.path.exists(model_path):
        print(f"   ❌ Piper model not found at {model_path}")
        return None

    try:
        test_text = "This is a benchmark test for Penny's voice"

        start = time.time()
        # Pipe text to piper command
        echo_process = subprocess.Popen(
            ["echo", test_text],
            stdout=subprocess.PIPE
        )

        piper_process = subprocess.run(
            ["piper", "--model", model_path, "--output_file", test_file],
            stdin=echo_process.stdout,
            capture_output=True,
            text=True,
            timeout=30
        )
        echo_process.stdout.close()
        latency = time.time() - start

        if piper_process.returncode == 0 and os.path.exists(test_file):
            file_size = os.path.getsize(test_file) / 1024  # KB
            print(f"   ✅ Latency: {latency:.2f}s")
            print(f"   Output: {test_file} ({file_size:.1f} KB)")

            # Clean up
            try:
                os.remove(test_file)
            except:
                pass

            return latency
        else:
            print(f"   ❌ Failed: {piper_process.stderr[:200]}")
            return None

    except subprocess.TimeoutExpired:
        print(f"   ❌ Timeout (>30s)")
        return None
    except FileNotFoundError:
        print(f"   ❌ Piper not installed (run: pip install piper-tts)")
        return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def check_system_resources():
    """Check available system resources"""
    print("\n💻 System Resources Check...")
    
    try:
        # Check RAM
        result = subprocess.run(
            ["sysctl", "hw.memsize"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            mem_bytes = int(result.stdout.split(':')[1].strip())
            mem_gb = mem_bytes / (1024**3)
            print(f"   Total RAM: {mem_gb:.1f} GB")
            
            if mem_gb >= 48:
                print(f"   ✅ Sufficient for LLaMA 70B")
            else:
                print(f"   ⚠️  May struggle with LLaMA 70B")
        
        # Check disk space
        result = subprocess.run(
            ["df", "-h", "/Users/CJ"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) >= 4:
                    available = parts[3]
                    print(f"   Available disk: {available}")
        
    except Exception as e:
        print(f"   ⚠️  Could not check system resources: {e}")

def main():
    print("=" * 70)
    print("🧪 PENNY EDGE AI STACK BENCHMARKS")
    print("=" * 70)
    print("\nThis will test the performance of all local AI models.")
    print("Expected time: 5-10 minutes\n")
    
    # Check system resources
    check_system_resources()
    
    benchmarks = {}
    
    # Test Ollama models
    print("\n" + "=" * 70)
    print("TESTING OLLAMA MODELS")
    print("=" * 70)
    
    benchmarks['llama3.1_8b'] = benchmark_ollama(
        "llama3.1:8b",
        "Say hello in exactly one sentence"
    )
    
    benchmarks['llama3.1_70b'] = benchmark_ollama(
        "llama3.1:70b-q4_K_M",
        "Say hello in exactly one sentence"
    )
    
    # Test Whisper
    print("\n" + "=" * 70)
    print("TESTING WHISPER.CPP")
    print("=" * 70)
    
    benchmarks['whisper_large_v3'] = benchmark_whisper()
    
    # Test TTS
    print("\n" + "=" * 70)
    print("TESTING PIPER TTS")
    print("=" * 70)

    benchmarks['piper_tts'] = benchmark_tts()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 BENCHMARK SUMMARY")
    print("=" * 70)
    
    for model, latency in benchmarks.items():
        status = "✅" if latency else "❌"
        latency_str = f"{latency:6.2f}s" if latency else "FAILED"
        print(f"   {status} {model:20s}: {latency_str}")
    
    # Calculate pipeline latencies
    print("\n" + "=" * 70)
    print("🎯 VOICE PIPELINE LATENCY ESTIMATES")
    print("=" * 70)
    
    stt = benchmarks.get('whisper_large_v3', 0)
    llm_fast = benchmarks.get('llama3.1_8b', 0)
    llm_smart = benchmarks.get('llama3.1_70b', 0)
    tts = benchmarks.get('piper_tts', 0)
    
    if all([stt, llm_fast, tts]):
        edge_fast = stt + llm_fast + tts
        print(f"\n   Edge Fast (8B):  {edge_fast:.2f}s")
        print(f"      STT: {stt:.2f}s + LLM: {llm_fast:.2f}s + TTS: {tts:.2f}s")
        
        if edge_fast < 1.0:
            print(f"      ✅ EXCELLENT! Meets <1s target")
        elif edge_fast < 1.5:
            print(f"      ✅ GOOD! Under 1.5s")
        else:
            print(f"      ⚠️  Exceeds 1.5s target")
    
    if all([stt, llm_smart, tts]):
        edge_smart = stt + llm_smart + tts
        print(f"\n   Edge Smart (70B): {edge_smart:.2f}s")
        print(f"      STT: {stt:.2f}s + LLM: {llm_smart:.2f}s + TTS: {tts:.2f}s")
        
        if edge_smart < 2.0:
            print(f"      ✅ EXCELLENT! Under 2s")
        elif edge_smart < 3.0:
            print(f"      ✅ GOOD! Under 3s")
        else:
            print(f"      ⚠️  Exceeds 3s target")
    
    # Cloud comparison
    print(f"\n   Cloud (GPT-4): ~3-5s (typical)")
    print(f"   Current Penny: ~3-5s (cloud-dependent)")
    
    if all([stt, llm_fast, tts]) and (stt + llm_fast + tts) < 1.5:
        improvement = 3.0 / (stt + llm_fast + tts)
        print(f"\n   🚀 Potential speedup: {improvement:.1f}x faster!")
    
    # Cost comparison
    print("\n" + "=" * 70)
    print("💰 COST COMPARISON (per 1000 interactions)")
    print("=" * 70)
    print(f"\n   Cloud-only: ~$30 (API fees)")
    print(f"   Edge-only:  ~$0.10 (electricity)")
    print(f"   Savings:    ~$29.90 (99.7%)")
    
    # Save results
    output_file = 'edge_benchmarks.json'
    try:
        with open(output_file, 'w') as f:
            json.dump({
                'benchmarks': benchmarks,
                'pipeline': {
                    'edge_fast': stt + llm_fast + tts if all([stt, llm_fast, tts]) else None,
                    'edge_smart': stt + llm_smart + tts if all([stt, llm_smart, tts]) else None
                },
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }, f, indent=2)
        print(f"\n💾 Results saved to {output_file}")
    except Exception as e:
        print(f"\n⚠️  Could not save results: {e}")
    
    print("\n" + "=" * 70)
    print("✨ BENCHMARK COMPLETE")
    print("=" * 70)
    
    # Final recommendation
    if all(benchmarks.values()):
        print("\n✅ ALL SYSTEMS OPERATIONAL!")
        print("   Ready for edge AI integration in Week 4.5")
    else:
        print("\n⚠️  SOME SYSTEMS FAILED")
        print("   Check installation guide: INSTALL_EDGE_AI_STACK.md")
        failed = [k for k, v in benchmarks.items() if not v]
        print(f"   Failed: {', '.join(failed)}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Benchmark cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
