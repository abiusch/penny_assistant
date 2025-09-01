# PennyGPT Troubleshooting Guide

Having issues with PennyGPT? This guide will help you diagnose and fix common problems.

## 🚀 Quick Diagnosis

Start with these automated diagnostic tools:

```bash
# Get system information
python system_info.py

# Run comprehensive health check
python check_health.py

# Run specific component tests
python -m pytest tests/test_health_monitor.py -v
```

## 🔧 Common Issues & Solutions

### LM Studio Connection Issues

**❌ Error: "Connection refused - LM Studio may not be running"**

**Solution:**
1. **Start LM Studio**: Download from [lmstudio.ai](https://lmstudio.ai) if not installed
2. **Start Local Server**: 
   - Go to Developer tab in LM Studio
   - Select a model (e.g., `microsoft/Phi-3-mini-4k-instruct-gguf`)
   - Click "Start Server"
   - Ensure port is set to 1234
3. **Test Connection**:
   ```bash
   curl -X GET http://localhost:1234/v1/models
   ```

**⚠️ Error: "Configured model not available"**

**Solution:**
1. **Check Available Models** in LM Studio Developer tab
2. **Update Configuration**: Edit `penny_config.json` to match exact model name:
   ```json
   {
     "llm": {
       "model": "microsoft/Phi-3-mini-4k-instruct-gguf"
     }
   }
   ```

**🐌 Error: "Request timed out - LM Studio may be overloaded"**

**Solution:**
1. **Close Other Applications** to free up RAM
2. **Use Smaller Model** (3B instead of 7B+ parameters)
3. **Enable GPU Acceleration** in LM Studio if available
4. **Increase Timeout** in configuration (not recommended):
   ```json
   {
     "timeouts": {
       "llm_timeout": 30.0
     }
   }
   ```

### TTS (Text-to-Speech) Issues

**❌ Error: "TTS synthesis failed"**

**Solution:**
1. **Check Internet Connection**: Google TTS requires internet
2. **Test gTTS Installation**:
   ```bash
   python -c "from gtts import gTTS; print('gTTS working')"
   ```
3. **Verify Audio Output**: Ensure speakers/headphones are connected
4. **Check Permissions**: Grant audio permissions to terminal/IDE

### STT (Speech-to-Text) Issues

**❌ Error: "Whisper model failed to load"**

**Solution:**
1. **Install Whisper**:
   ```bash
   pip install openai-whisper
   ```
2. **Free Disk Space**: Whisper models need ~1-5GB depending on size
3. **Test Model Loading**:
   ```bash
   python -c "import whisper; model = whisper.load_model('base'); print('Whisper working')"
   ```
4. **Try Smaller Model**: Change in `penny_config.json`:
   ```json
   {
     "stt": {
       "model": "tiny"
     }
   }
   ```

### Audio Device Issues

**❌ Error: "No suitable audio devices found"**

**Solution:**
1. **Connect Microphone and Speakers**
2. **Test Audio Devices**:
   ```bash
   python -c "import sounddevice as sd; print(sd.query_devices())"
   ```
3. **Check System Permissions**: Grant microphone access
4. **Install Audio Dependencies** (Linux):
   ```bash
   sudo apt-get install portaudio19-dev python3-pyaudio
   ```

### Python Environment Issues

**❌ Error: "Module not found"**

**Solution:**
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Check Python Path**: Ensure you're in the project directory
3. **Virtual Environment**: Activate if using one:
   ```bash
   source .venv/bin/activate  # Unix/macOS
   .venv\Scripts\activate     # Windows
   ```

## 🔍 Advanced Debugging

### Enable Detailed Logging

Add to `penny_config.json`:
```json
{
  "debug": {
    "verbose_logging": true,
    "log_audio_pipeline": true,
    "log_llm_requests": true
  }
}
```

### Component-Specific Testing

**Test LLM Only:**
```bash
python -c "
from src.adapters.llm.openai_compat import OpenAICompatLLM
import json
config = json.load(open('penny_config.json'))
llm = OpenAICompatLLM(config)
print(llm.complete('Say hello'))
"
```

**Test TTS Only:**
```bash
python -c "
from src.adapters.tts.google_tts_adapter import GoogleTTS
import json
config = json.load(open('penny_config.json'))
tts = GoogleTTS(config)
tts.speak('Testing TTS')
"
```

**Test STT Only:**
```bash
python -c "
from src.adapters.stt.whisper_adapter import WhisperSTT
import json
config = json.load(open('penny_config.json'))
stt = WhisperSTT(config)
print('STT model loaded:', stt._model is not None)
"
```

### Performance Profiling

**Monitor Resource Usage:**
```bash
# macOS/Linux
top -pid $(pgrep -f "python.*penny")

# Windows
tasklist /FI "IMAGENAME eq python*"
```

**Check Network Connections:**
```bash
# macOS/Linux
lsof -i :1234

# Windows  
netstat -an | findstr :1234
```

## 🛠️ Configuration Tuning

### For Low-End Systems
```json
{
  "llm": {
    "model": "microsoft/Phi-3-mini-4k-instruct-gguf",
    "max_tokens": 256
  },
  "stt": {
    "model": "tiny"
  },
  "timeouts": {
    "llm_timeout": 45.0
  }
}
```

### For High-End Systems
```json
{
  "llm": {
    "model": "meta-llama/Llama-2-13b-chat-hf",
    "max_tokens": 1024,
    "temperature": 0.7
  },
  "stt": {
    "model": "medium"
  },
  "timeouts": {
    "llm_timeout": 10.0
  }
}
```

## 🆘 Getting Help

If you're still having issues:

1. **Run Full Diagnostics**:
   ```bash
   python system_info.py
   python check_health.py
   ```

2. **Check Logs**: Look for error messages in console output

3. **Test Individual Components**: Use the component-specific tests above

4. **Review Configuration**: Ensure `penny_config.json` matches your system

5. **Check Dependencies**: Verify all requirements are installed

## 📋 Health Check Checklist

Before reporting issues, ensure:
- [ ] LM Studio is running with correct model
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Audio devices connected and permissions granted
- [ ] Internet connection available for TTS
- [ ] Sufficient disk space for models (5GB+)
- [ ] Python 3.11+ (avoid 3.13+ for better compatibility)

---

**Still need help?** Include the output of `python system_info.py` and `python check_health.py` when asking for support.
