# PennyGPT - Local Voice Assistant

A privacy-focused voice assistant that runs entirely on your local machine using LM Studio for language processing.

## Features

- **🎙️ Voice Interaction**: Wake word detection and speech recognition
- **🤖 Local LLM**: Powered by LM Studio with OpenAI-compatible API
- **🔒 Privacy First**: All processing happens locally, no cloud dependencies
- **📅 Smart Plugins**: Calendar integration, weather, calculations, and more
- **⚡ Fast Response**: Optimized pipeline with caching and background processing
- **🎨 Personality**: Configurable response style and tone

## Quick Start

### 1. Install Dependencies

```bash
# Clone the repository
git clone <repository-url>
cd penny_assistant

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Set Up LM Studio

1. Download and install [LM Studio](https://lmstudio.ai)
2. Download a model (recommended: `microsoft/Phi-3-mini-4k-instruct-gguf`)
3. Start the local server on port 1234

**Quick Test:**
```bash
# Verify LM Studio is running
curl -X GET http://localhost:1234/v1/models

# Test chat completion
curl -X POST http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer lm-studio" \
  -d '{
    "model": "microsoft/Phi-3-mini-4k-instruct-gguf",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 50
  }'
```

### 3. Configure PennyGPT

The configuration is already set up in `penny_config.json`. Just ensure the model name matches your LM Studio model:

```json
{
  "llm": {
    "provider": "openai_compatible",
    "base_url": "http://localhost:1234/v1",
    "api_key": "lm-studio",
    "model": "microsoft/Phi-3-mini-4k-instruct-gguf",
    "temperature": 0.6,
    "max_tokens": 512
  }
}
```

### 4. Test the System

```bash
# Run tests to verify everything works
python -m pytest tests/test_openai_compat_llm.py -v
python -m pytest tests/test_tts_pipeline.py -v
python -m pytest tests/test_wake_word.py -v

# Test basic LLM integration
python -c "from src.adapters.llm.openai_compat import OpenAICompatLLM; import json; config = json.load(open('penny_config.json')); llm = OpenAICompatLLM(config); print(llm.complete('Hello, how are you?'))"
```

## Architecture

### Core Components

- **Pipeline**: State machine managing the conversation flow (IDLE → LISTENING → THINKING → SPEAKING)
- **STT**: Speech-to-text using Whisper for voice input
- **LLM**: Language model integration via LM Studio's OpenAI-compatible API
- **TTS**: Text-to-speech with Google TTS, including caching and background playback
- **VAD**: Voice activity detection to trigger listening
- **Wake Word**: "Hey Penny" detection with command extraction

### Key Features

**🔧 Robust Error Handling:**
- Graceful degradation when components fail
- Comprehensive logging and telemetry
- Timeout protection and fallback mechanisms

**⚡ Performance Optimizations:**
- TTS caching for common phrases
- Background audio playback
- Efficient wake word processing
- Optimized timeouts (15s for LLM, 1s for calendar)

**🎛️ Configurable:**
- Personality settings (sarcasm, humor style)
- Model parameters (temperature, max tokens)
- Plugin routing and fallback behavior
- Audio device and quality settings

## Plugin System

### Built-in Plugins

- **Calendar**: macOS Calendar integration with reliable fallback
- **Weather**: Current conditions and forecasts  
- **Shell**: Safe command execution with timeouts
- **Calculations**: Math and unit conversions

### Plugin Development

```python
from src.plugins.base_plugin import BasePlugin

class MyPlugin(BasePlugin):
    def can_handle(self, intent: str, query: str) -> bool:
        return "my_keyword" in query.lower()
    
    async def execute(self, query: str, context: dict = None) -> dict:
        return {
            "success": True,
            "response": "My plugin response",
            "data": {}
        }
```

## Configuration

### Core Settings

```json
{
  "wake_word": "penny",
  "stt": {
    "type": "whisper",
    "model": "base",
    "language": "en"
  },
  "tts": {
    "type": "google",
    "cache_enabled": true,
    "preload_common_phrases": true
  },
  "personality": {
    "sarcasm_level": 0.3,
    "humor_style": "witty"
  },
  "timeouts": {
    "llm_timeout": 15.0,
    "tts_timeout": 10.0
  }
}
```

### Advanced Options

- **Audio**: Input device selection and calibration
- **Routing**: Intent classification and plugin selection
- **Memory**: Conversation context and history
- **Telemetry**: Performance monitoring and debugging

## Documentation

- **[LM Studio Setup](docs/SETUP_LM_STUDIO.md)**: Complete guide to configuring local LLM
- **[macOS Permissions](docs/SETUP_LM_STUDIO.md#macos-permissions-and-automation)**: System integration requirements
- **Plugin API**: Development guide for custom plugins
- **Voice Calibration**: Microphone and audio setup

## Development

### Running Tests

```bash
# Full test suite
python -m pytest tests/ -v

# Specific components
python -m pytest tests/test_openai_compat_llm.py -v  # LLM integration
python -m pytest tests/test_tts_pipeline.py -v       # TTS reliability
python -m pytest tests/test_wake_word.py -v          # Wake word detection
python -m pytest tests/test_calendar_fallback.py -v  # Calendar plugin

# Integration tests (requires LM Studio running)
python -m pytest tests/ -v -k integration
```

### Code Quality

```bash
# Run pre-commit hooks
pre-commit run --all-files

# Type checking
mypy src/

# Format code
black src/ tests/
```

### Debugging

Enable verbose logging in `penny_config.json`:

```json
{
  "debug": {
    "verbose_logging": true,
    "log_audio_pipeline": true,
    "log_llm_requests": true
  }
}
```

## Troubleshooting

### Common Issues

**LM Studio Connection:**
```bash
# Check if server is running
curl -X GET http://localhost:1234/v1/models

# Verify model name matches configuration
grep -A 10 '"llm"' penny_config.json
```

**Audio Issues:**
```bash
# Test microphone
python debug_audio.py

# Calibrate audio levels
python audio_calibrate.py
```

**macOS Permissions:**
- Grant microphone access to Terminal/IDE
- Allow Calendar automation in System Settings
- Enable Accessibility permissions for system control

### Performance Issues

**Slow Responses:**
- Use a smaller/faster model in LM Studio
- Reduce `max_tokens` in configuration
- Close other applications to free RAM
- Enable GPU acceleration if available

**Memory Usage:**
- Monitor with `htop` or Activity Monitor
- Consider quantized models (Q4_K_M, Q5_K_M)
- Enable model offloading in LM Studio

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`python -m pytest tests/ -v`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

### Development Workflow

- **Code Style**: Black formatting, type hints preferred
- **Testing**: Add tests for new features, maintain >90% coverage
- **Documentation**: Update relevant docs and docstrings
- **Performance**: Profile changes, avoid blocking operations

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **LM Studio** for providing excellent local LLM hosting
- **OpenAI** for the API specification and model architectures
- **Whisper** for robust speech recognition
- **Contributors** who help improve PennyGPT

## Roadmap

- [ ] **Streaming TTS**: Real-time audio generation
- [ ] **Multi-language**: Support for additional languages
- [ ] **Advanced Plugins**: Home automation, file management
- [ ] **Mobile Support**: iOS/Android companion apps
- [ ] **Voice Training**: Personalized wake word detection
- [ ] **Memory System**: Long-term conversation context

---

**Need Help?** Check the [documentation](docs/), run the test suite, or open an issue with detailed error logs and system information.
