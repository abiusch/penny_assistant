# 🚀 MAXIMUM SPEED INSTALLATION - EXECUTE NOW

**Status:** Ready to install Whisper.cpp and Coqui TTS  
**Location:** VS Code Terminal  
**Time:** ~35 minutes total

---

## 📋 **CURRENT STATUS:**

```
✅ Ollama installed (v0.12.3)
⏳ LLaMA models downloading (Terminal - let it finish)
⏳ Whisper.cpp - READY TO INSTALL
⏳ Coqui TTS - READY TO INSTALL
```

---

## 🎯 **INSTALLATION STEPS (IN VS CODE)**

### **Step 1: Open VS Code Terminal**

1. VS Code should be open now
2. Press **`Ctrl + ` `** (Control + Backtick) to open integrated terminal
3. Make sure you're in the project directory:

```bash
cd /Users/CJ/Desktop/penny_assistant
```

---

### **Step 2: Install Whisper.cpp (~20 minutes)**

**Run this command:**

```bash
./install_whisper_cpp.sh
```

**What will happen:**
- Clones whisper.cpp repository
- Builds with Metal acceleration (M4 Pro optimized)
- Downloads large-v3 model (~3GB)
- Tests with sample audio
- **Time:** ~20 minutes (mostly downloading)

**Expected output:**
```
🎤 Installing Whisper.cpp...
📥 Cloning repository...
🔨 Building with Metal...
📥 Downloading model (3GB)...
🧪 Testing...
✅ Whisper.cpp ready!
```

---

### **Step 3: Install Coqui TTS (~15 minutes)**

**After Whisper.cpp finishes, run:**

```bash
./install_coqui_tts.sh
```

**What will happen:**
- Installs TTS Python library
- Downloads XTTS v2 model (~2GB, first run only)
- Generates test audio
- Plays Penny's voice sample
- **Time:** ~15 minutes (first run)

**Expected output:**
```
🔊 Installing Coqui TTS...
📥 Installing library...
🧪 Testing (downloading model)...
🔊 Playing sample...
✅ Coqui TTS ready!
```

---

### **Step 4: Run Full Benchmarks (~5 minutes)**

**After both are installed, run:**

```bash
python3 benchmark_edge_models.py
```

**What it tests:**
- LLaMA 3.1 8B speed
- LLaMA 3.1 70B speed  
- Whisper.cpp speed
- Coqui TTS speed
- Total pipeline latency

**Expected results:**
```
📊 BENCHMARK SUMMARY
═══════════════════════════════════════════
   ✅ llama3.1_8b         :   0.30s
   ✅ llama3.1_70b        :   1.50s
   ✅ whisper_large_v3    :   0.20s
   ✅ coqui_xtts          :   0.30s

🎯 VOICE PIPELINE LATENCY:
   Edge Fast (8B):  0.80s  ✅ EXCELLENT!
   Edge Smart (70B): 2.00s  ✅ EXCELLENT!

🚀 5x faster than cloud!
💰 99.7% cost savings!
```

---

## ⏰ **TIMELINE:**

```
Now:                Ollama models downloading in Terminal
                    ↓
In 5 min:          Start Whisper.cpp install (VS Code)
                    ↓ (20 min)
In 25 min:         Start Coqui TTS install
                    ↓ (15 min)
In 40 min:         Run benchmarks
                    ↓ (5 min)
In 45 min:         ALL DONE! ✅
```

---

## 🎯 **QUICK START (COPY-PASTE INTO VS CODE TERMINAL):**

```bash
# Navigate to project
cd /Users/CJ/Desktop/penny_assistant

# Install Whisper.cpp
./install_whisper_cpp.sh

# Install Coqui TTS (after Whisper finishes)
./install_coqui_tts.sh

# Run benchmarks (after both finish)
python3 benchmark_edge_models.py
```

---

## 🐛 **IF SOMETHING FAILS:**

### **Whisper.cpp build fails:**
```bash
# Install Xcode command line tools
xcode-select --install
# Then retry
./install_whisper_cpp.sh
```

### **TTS install fails:**
```bash
# Use venv
source .venv/bin/activate
pip install TTS
```

### **Benchmarks fail:**
```bash
# Make sure all steps completed
# Check: ls -la whisper.cpp/main
# Check: python3 -c "import TTS"
```

---

## ✅ **SUCCESS CRITERIA:**

After all installations:

1. ✅ `whisper.cpp/main` exists
2. ✅ `whisper.cpp/models/ggml-large-v3.bin` exists (~3GB)
3. ✅ `python3 -c "import TTS"` works
4. ✅ `test_penny_voice.wav` created and plays
5. ✅ Benchmarks show <1s edge fast pipeline
6. ✅ `edge_benchmarks.json` created

---

## 🚀 **READY?**

**Open VS Code Terminal (Ctrl + `) and run:**

```bash
cd /Users/CJ/Desktop/penny_assistant && ./install_whisper_cpp.sh
```

**I'll be here if you need help!** ✨

---

**Let's make Penny FAST!** ⚡💜
