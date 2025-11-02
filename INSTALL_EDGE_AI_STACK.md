# EDGE AI STACK INSTALLATION GUIDE

**Date:** October 28, 2025  
**Hardware:** M4 Pro 48GB RAM  
**Time Required:** 2-4 hours (mostly downloading)  
**Disk Space:** ~50GB

---

## 🎯 **WHAT WE'RE INSTALLING**

```
Edge AI Stack for Penny:
├── Ollama (Local LLM runtime)
│   ├── LLaMA 3.1 8B (~5GB)
│   └── LLaMA 3.1 70B-Q4 (~40GB)
├── Whisper.cpp (Local STT)
│   └── large-v3 model (~3GB)
└── Coqui TTS (Local TTS)
    └── XTTS v2 (~2GB)

Total: ~50GB disk, ~35-45GB RAM active
```

---

## 📦 **STEP 1: INSTALL OLLAMA**

### **Download:**
1. Open browser: https://ollama.ai/download
2. Click "Download for macOS"
3. Open the .dmg file
4. Drag Ollama to Applications

### **Verify Installation:**
```bash
# Open Terminal
ollama --version
# Should show: ollama version 0.x.x
```

### **Pull Models:**
```bash
# Pull fast model (8B, ~5GB, takes 5-10 min)
ollama pull llama3.1:8b

# Pull smart model (70B quantized, ~40GB, takes 30-60 min)
ollama pull llama3.1:70b-q4_K_M

# Verify
ollama list
```

### **Test:**
```bash
# Test fast model
ollama run llama3.1:8b "Hello, tell me a joke in one sentence"

# Test smart model (this will take longer)
ollama run llama3.1:70b-q4_K_M "Explain quantum entanglement briefly"
```

**Expected Output:**
- Fast model: Response in ~2-3 seconds
- Smart model: Response in ~5-10 seconds (first load slower)

---

## 📦 **STEP 2: INSTALL WHISPER.CPP**

### **Clone and Build:**
```bash
cd /Users/CJ/Desktop/penny_assistant

# Clone repository
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp

# Build (uses Metal for M4 Pro acceleration)
make

# Should see: whisper.cpp built successfully
```

### **Download Model:**
```bash
# Download large-v3 model (~3GB)
bash ./models/download-ggml-model.sh large-v3

# Verify
ls -lh models/ggml-large-v3.bin
# Should show: ~3GB file
```

### **Test:**
```bash
# Test with sample audio
./main -m models/ggml-large-v3.bin -f samples/jfk.wav

# Should transcribe JFK speech
```

**Expected Output:**
- Transcription appears within 2-5 seconds
- "And so my fellow Americans..." text

---

## 📦 **STEP 3: INSTALL COQUI TTS**

### **Install via pip:**
```bash
cd /Users/CJ/Desktop/penny_assistant

# Install TTS library
/opt/homebrew/bin/pip3 install --break-system-packages TTS

# This may take 10-15 minutes
```

### **Test:**
```bash
# Test synthesis
tts --text "Hello, I'm Penny, your AI assistant" \
    --model_name tts_models/multilingual/multi-dataset/xtts_v2 \
    --out_path test_penny_voice.wav

# Play the audio
afplay test_penny_voice.wav
```

**Expected Output:**
- First run downloads model (~2GB, 5-10 min)
- Generates audio file
- Audio plays with synthesized voice

---

## 🧪 **STEP 4: BENCHMARK ALL MODELS**

### **Create Benchmark Script:**

Save this as `benchmark_edge_models.py`:

```python
#!/usr/bin/env python3
"""Benchmark all edge AI models"""

import subprocess
import time
import json

def benchmark_ollama(model_name, prompt):
    """Benchmark Ollama model"""
    print(f"\n🧠 Benchmarking {model_name}...")
    
    start = time.time()
    result = subprocess.run(
        ["ollama", "run", model_name, prompt],
        capture_output=True,
        text=True
    )
    latency = time.time() - start
    
    print(f"   Latency: {latency:.2f}s")
    print(f"   Output: {result.stdout[:100]}...")
    
    return latency

def benchmark_whisper():
    """Benchmark Whisper.cpp"""
    print(f"\n🎤 Benchmarking Whisper.cpp...")
    
    # Use sample audio
    start = time.time()
    result = subprocess.run(
        ["./whisper.cpp/main", "-m", "whisper.cpp/models/ggml-large-v3.bin", 
         "-f", "whisper.cpp/samples/jfk.wav"],
        capture_output=True,
        text=True
    )
    latency = time.time() - start
    
    print(f"   Latency: {latency:.2f}s")
    
    return latency

def benchmark_tts():
    """Benchmark Coqui TTS"""
    print(f"\n🔊 Benchmarking Coqui TTS...")
    
    start = time.time()
    result = subprocess.run([
        "tts",
        "--text", "This is a benchmark test",
        "--model_name", "tts_models/multilingual/multi-dataset/xtts_v2",
        "--out_path", "benchmark_tts.wav"
    ], capture_output=True)
    latency = time.time() - start
    
    print(f"   Latency: {latency:.2f}s")
    
    return latency

def main():
    print("=" * 60)
    print("🧪 EDGE AI STACK BENCHMARKS")
    print("=" * 60)
    
    benchmarks = {}
    
    # Test Ollama models
    benchmarks['llama3.1_8b'] = benchmark_ollama(
        "llama3.1:8b",
        "Say hello in one sentence"
    )
    
    benchmarks['llama3.1_70b'] = benchmark_ollama(
        "llama3.1:70b-q4_K_M",
        "Say hello in one sentence"
    )
    
    # Test Whisper
    try:
        benchmarks['whisper_large_v3'] = benchmark_whisper()
    except Exception as e:
        print(f"   Whisper benchmark failed: {e}")
        benchmarks['whisper_large_v3'] = None
    
    # Test TTS
    try:
        benchmarks['coqui_xtts'] = benchmark_tts()
    except Exception as e:
        print(f"   TTS benchmark failed: {e}")
        benchmarks['coqui_xtts'] = None
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 BENCHMARK SUMMARY")
    print("=" * 60)
    
    for model, latency in benchmarks.items():
        if latency:
            print(f"   {model:20s}: {latency:6.2f}s")
        else:
            print(f"   {model:20s}: FAILED")
    
    # Calculate total stack latency
    if all(benchmarks.values()):
        stt_latency = benchmarks.get('whisper_large_v3', 0)
        llm_fast = benchmarks.get('llama3.1_8b', 0)
        llm_smart = benchmarks.get('llama3.1_70b', 0)
        tts_latency = benchmarks.get('coqui_xtts', 0)
        
        edge_fast_total = stt_latency + llm_fast + tts_latency
        edge_smart_total = stt_latency + llm_smart + tts_latency
        
        print(f"\n🎯 TOTAL VOICE PIPELINE LATENCY:")
        print(f"   Edge Fast (8B):  {edge_fast_total:.2f}s")
        print(f"   Edge Smart (70B): {edge_smart_total:.2f}s")
        
        if edge_fast_total < 1.0:
            print(f"\n✅ EXCELLENT! Edge Fast meets <1s target!")
        elif edge_fast_total < 2.0:
            print(f"\n✅ GOOD! Edge Fast under 2s target")
        else:
            print(f"\n⚠️  Edge Fast exceeds targets, may need optimization")
    
    print("=" * 60)
    
    # Save results
    with open('edge_benchmarks.json', 'w') as f:
        json.dump(benchmarks, f, indent=2)
    
    print(f"\n💾 Results saved to edge_benchmarks.json")

if __name__ == "__main__":
    main()
```

### **Run Benchmarks:**
```bash
cd /Users/CJ/Desktop/penny_assistant
chmod +x benchmark_edge_models.py
python3 benchmark_edge_models.py
```

**Expected Results:**
```
📊 BENCHMARK SUMMARY
============================================================
   llama3.1_8b         :   0.40s
   llama3.1_70b        :   1.50s
   whisper_large_v3    :   0.20s
   coqui_xtts          :   0.30s

🎯 TOTAL VOICE PIPELINE LATENCY:
   Edge Fast (8B):  0.90s  ✅
   Edge Smart (70B): 2.00s  ✅
```

---

## ✅ **SUCCESS CRITERIA**

After installation, you should have:

### **1. Ollama Working:**
```bash
ollama list
# Shows: llama3.1:8b and llama3.1:70b-q4_K_M

ollama run llama3.1:8b "Hi"
# Returns: Response in < 3s
```

### **2. Whisper Working:**
```bash
./whisper.cpp/main -m whisper.cpp/models/ggml-large-v3.bin -f whisper.cpp/samples/jfk.wav
# Shows: Transcribed text
```

### **3. TTS Working:**
```bash
tts --text "Test" --model_name tts_models/multilingual/multi-dataset/xtts_v2 --out_path test.wav
afplay test.wav
# Plays: Synthesized speech
```

### **4. Benchmarks:**
- LLaMA 8B: < 1s
- LLaMA 70B: < 3s
- Whisper: < 0.5s
- TTS: < 0.5s
- **Total Edge Fast Pipeline: < 1.5s** ✅

---

## 🐛 **TROUBLESHOOTING**

### **Ollama Issues:**

**Problem:** "ollama: command not found"  
**Solution:** Add to PATH: `export PATH=$PATH:/Applications/Ollama.app/Contents/MacOS`

**Problem:** Model download fails  
**Solution:** Check internet, try again, or download manually from ollama.ai

### **Whisper.cpp Issues:**

**Problem:** Build fails  
**Solution:** Install Xcode command line tools: `xcode-select --install`

**Problem:** Metal not found  
**Solution:** M4 Pro should have Metal. Check: `system_profiler SPDisplaysDataType`

### **TTS Issues:**

**Problem:** pip install fails  
**Solution:** Use `--break-system-packages` flag or create venv

**Problem:** Model download slow  
**Solution:** First run downloads ~2GB, be patient. Subsequent runs are fast.

---

## 📊 **DISK SPACE CHECK**

Before starting:
```bash
df -h /Users/CJ
# Need: 50GB free
```

After installation:
```bash
du -sh ~/.ollama
# Should show: ~45GB

du -sh whisper.cpp/models
# Should show: ~3GB

du -sh ~/.local/share/tts
# Should show: ~2GB
```

---

## 🎉 **COMPLETION CHECKLIST**

- [ ] Ollama installed and tested
- [ ] LLaMA 3.1 8B pulled and working
- [ ] LLaMA 3.1 70B pulled and working
- [ ] Whisper.cpp built and tested
- [ ] Whisper large-v3 model downloaded
- [ ] Coqui TTS installed and tested
- [ ] XTTS v2 model downloaded
- [ ] Benchmarks run and results saved
- [ ] All benchmarks < 3s
- [ ] Total edge fast pipeline < 1.5s

---

## 🚀 **NEXT STEPS AFTER INSTALLATION**

Once all benchmarks pass:

1. **Update NEXT_PHASE_TASKS.md** - Mark edge setup complete
2. **Create EdgeModelLoader** - Week 4.5 infrastructure
3. **Build HybridRouter** - Smart routing logic
4. **Integrate with Pipeline** - EdgeModalInterface
5. **Test Voice Pipeline** - End-to-end with edge models

---

## 📝 **NOTES**

**Installation Order Matters:**
1. Ollama first (easiest, validates GPU)
2. Whisper next (tests build system)
3. TTS last (most dependencies)

**First Run Slow:**
- Models compile/optimize on first load
- Subsequent runs much faster
- This is normal!

**M4 Pro Advantages:**
- Unified memory = fast model switching
- Metal acceleration = fast inference
- 48GB RAM = can run 70B comfortably

---

**Ready to install? Let's go! 🚀✨**

**Estimated total time: 2-4 hours (mostly downloads)**
