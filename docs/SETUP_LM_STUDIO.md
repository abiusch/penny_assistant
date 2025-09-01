# LM Studio Setup Guide for PennyGPT

This guide walks through setting up LM Studio to work with PennyGPT's local LLM capabilities.

## Overview

LM Studio provides a local OpenAI-compatible API server that PennyGPT can use instead of cloud-based language models. This setup offers:

- **Privacy**: All processing happens locally
- **Cost Control**: No API usage fees
- **Offline Operation**: Works without internet connection
- **Customization**: Use any compatible model

## Prerequisites

- macOS, Windows, or Linux computer with sufficient RAM (8GB+ recommended)
- LM Studio application installed
- A compatible language model (GGUF format recommended)

## Installation Steps

### 1. Download and Install LM Studio

1. Visit [lmstudio.ai](https://lmstudio.ai) and download LM Studio
2. Install the application following the standard process for your operating system
3. Launch LM Studio

### 2. Download a Model

1. In LM Studio, go to the **Discover** tab
2. Search for a model suitable for your hardware:
   - For 8GB RAM: `microsoft/Phi-3-mini-4k-instruct-gguf` or similar 3-7B parameter models
   - For 16GB+ RAM: `microsoft/Phi-3-medium-4k-instruct-gguf` or larger models
   - For powerful systems: `meta-llama/Llama-2-13b-chat-gguf` or similar

3. Click **Download** and wait for the model to download
4. Note the exact model name (e.g., `microsoft/Phi-3-mini-4k-instruct-gguf`)

### 3. Start the Local Server

1. Go to the **Developer** tab in LM Studio
2. Click **Select a model** and choose your downloaded model
3. Configure server settings:
   - **Port**: Set to `1234` (default)
   - **CORS**: Enable if needed
   - **Authentication**: Can be disabled for local use

4. Click **Start Server**
5. You should see a message like "Local server running on port 1234"

### 4. Verify Server is Running

Open a terminal and test the server:

```bash
# Test that the server is accessible
curl -X GET http://localhost:1234/v1/models

# Test a simple completion
curl -X POST http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer lm-studio" \
  -d '{
    "model": "microsoft/Phi-3-mini-4k-instruct-gguf",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Say hello"}
    ],
    "temperature": 0.7,
    "max_tokens": 50
  }'
```

Expected response should include model information and a chat completion.

## Configure PennyGPT

### 1. Update Configuration

Edit your `penny_config.json` file to use the LM Studio server:

```json
{
  "llm": {
    "provider": "openai_compatible",
    "base_url": "http://localhost:1234/v1",
    "api_key": "lm-studio",
    "model": "microsoft/Phi-3-mini-4k-instruct-gguf",
    "mode": "local_first",
    "temperature": 0.6,
    "max_tokens": 512
  }
}
```

**Important Configuration Notes:**

- `provider`: Must be exactly `"openai_compatible"`, `"openai-compatible"`, or `"lmstudio"`
- `base_url`: Should include the `/v1` path
- `api_key`: Can be any string (LM Studio ignores the value but requires the header)
- `model`: Must exactly match the model name shown in LM Studio
- `temperature`: 0.0-1.0, controls randomness (0.6 is a good default)
- `max_tokens`: Maximum response length (512 is reasonable for conversation)

### 2. Test PennyGPT Integration

Run the PennyGPT test suite to verify integration:

```bash
# Run LLM-specific tests
python -m pytest tests/test_openai_compat_llm.py -v

# Test basic functionality
python -c "from src.adapters.llm.openai_compat import OpenAICompatLLM; import json; config = json.load(open('penny_config.json')); llm = OpenAICompatLLM(config); print(llm.complete('Hello, how are you?'))"
```

## Troubleshooting

### Common Issues

**1. Connection Refused**
```
requests.exceptions.ConnectionError: HTTPSConnectionPool(host='localhost', port=1234)
```
- Ensure LM Studio server is running (check Developer tab)
- Verify port 1234 is not blocked by firewall
- Try restarting LM Studio

**2. Model Not Found**
```
{"error": {"message": "Model not found"}}
```
- Check that the model name in `penny_config.json` exactly matches the name in LM Studio
- Ensure the model is loaded in the Developer tab

**3. Slow Responses**
```
requests.exceptions.ReadTimeout: HTTPSConnectionPool read timed out
```
- Reduce `max_tokens` in configuration
- Use a smaller/faster model
- Increase timeout in PennyGPT configuration
- Close other applications to free up RAM

**4. High Memory Usage**
```
System becomes slow or unresponsive
```
- Use a smaller model (fewer parameters)
- Close other applications
- Consider upgrading system RAM
- Enable model offloading in LM Studio settings

### Performance Optimization

**Model Selection Guidelines:**
- **3B parameters**: Fast, works on 8GB RAM, good for basic tasks
- **7B parameters**: Balanced performance, needs 12GB+ RAM
- **13B+ parameters**: High quality, requires 16GB+ RAM

**LM Studio Settings:**
- Enable **GPU acceleration** if available
- Adjust **context length** based on your needs
- Use **quantized models** (Q4_K_M, Q5_K_M) for better performance
- Enable **model offloading** for larger models

**System Optimization:**
- Close unnecessary applications
- Monitor RAM usage during operation
- Consider SSD storage for model files
- Disable other AI applications while running

## Model Recommendations

### For Conversation (Recommended for PennyGPT)

**Lightweight (8GB RAM):**
- `microsoft/Phi-3-mini-4k-instruct-gguf` - Excellent for conversation
- `microsoft/Phi-3.5-mini-instruct-gguf` - Updated version with better performance
- `Qwen/Qwen2-7B-Instruct-GGUF` - Good multilingual support

**Balanced (12-16GB RAM):**
- `microsoft/Phi-3-medium-4k-instruct-gguf` - Great balance of speed and quality
- `meta-llama/Llama-2-7b-chat-hf` - Popular, well-tested model
- `mistralai/Mistral-7B-Instruct-v0.3` - Fast and capable

**High Quality (16GB+ RAM):**
- `meta-llama/Llama-2-13b-chat-hf` - Excellent quality
- `mistralai/Mixtral-8x7B-Instruct-v0.1` - State-of-the-art performance
- `NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO` - Fine-tuned for helpfulness

### Model Format Notes

- **GGUF format**: Preferred for LM Studio (quantized, optimized)
- **Quantization levels**: Q4_K_M (balanced), Q5_K_M (higher quality), Q8_0 (near full precision)
- **Context length**: 4k (standard), 8k+ (longer conversations, more memory)

## Advanced Configuration

### Custom Model Parameters

You can fine-tune model behavior in LM Studio's Developer tab:

```json
{
  "temperature": 0.7,
  "top_p": 0.9,
  "top_k": 40,
  "repeat_penalty": 1.1,
  "max_tokens": 512
}
```

### Multiple Models

To use different models for different tasks:

1. Download multiple models in LM Studio
2. Switch models in the Developer tab as needed
3. Update `penny_config.json` with the new model name
4. Restart PennyGPT to pick up changes

### API Compatibility

LM Studio implements most OpenAI API endpoints:

- `GET /v1/models` - List available models
- `POST /v1/chat/completions` - Chat completions (used by PennyGPT)
- `POST /v1/completions` - Text completions
- `POST /v1/embeddings` - Text embeddings (if model supports)

## Security Considerations

### Local Network Access

**Default (Recommended):**
- LM Studio runs on `localhost` only
- Not accessible from other devices
- Safe for personal use

**Network Access (Advanced):**
- Can configure LM Studio to accept external connections
- Use with caution - no built-in authentication
- Consider firewall rules and VPN access

### Data Privacy

**Advantages:**
- All processing happens locally
- No data sent to external servers
- Complete privacy and control
- Works offline

**Considerations:**
- Model training data may contain biases
- No content filtering by default
- User responsible for appropriate use

## macOS Permissions and Automation

If you plan to use PennyGPT's calendar or other system integration features alongside LM Studio, you may need to configure permissions:

### System Preferences Setup

1. **System Settings → Privacy & Security → Automation**
   - Allow Terminal or your IDE to control Calendar, if needed
   - Allow PennyGPT to access system features

2. **System Settings → Privacy & Security → Accessibility**
   - Add Terminal or your development environment if voice control is used
   - This enables system automation features

3. **Microphone and Speech Recognition**
   - Allow PennyGPT access to microphone for voice input
   - Enable speech recognition if using voice features

### Troubleshooting Permissions

If you see automation prompts or timeouts:
- Grant permissions when prompted
- Check System Settings for any blocked applications
- Restart applications after granting permissions
- Consider using the calendar fallback mode for reliability

## Integration Examples

### Basic Chat Test

```python
# Test script for LM Studio integration
from src.adapters.llm.openai_compat import OpenAICompatLLM
import json

# Load configuration
with open('penny_config.json', 'r') as f:
    config = json.load(f)

# Create LLM instance
llm = OpenAICompatLLM(config)

# Test basic completion
response = llm.complete("Hello, how are you today?", tone="friendly")
print(f"Response: {response}")

# Test with different tones
tones = ["helpful", "humorous", "professional"]
for tone in tones:
    response = llm.complete("Tell me about artificial intelligence", tone=tone)
    print(f"\n{tone.title()} tone: {response}")
```

### Conversation Loop

```python
# Interactive conversation with LM Studio
from src.adapters.llm.openai_compat import OpenAICompatLLM
import json

with open('penny_config.json', 'r') as f:
    config = json.load(f)

llm = OpenAICompatLLM(config)

print("Chat with PennyGPT (type 'quit' to exit)")
while True:
    user_input = input("\nYou: ")
    if user_input.lower() in ['quit', 'exit', 'bye']:
        break
    
    response = llm.complete(user_input, tone="conversational")
    print(f"Penny: {response}")
```

## FAQ

**Q: Can I use multiple models simultaneously?**
A: LM Studio runs one model at a time, but you can quickly switch between downloaded models.

**Q: How much disk space do models require?**
A: Varies by model size and quantization. 3B models: ~2-4GB, 7B models: ~4-8GB, 13B+ models: 8GB+.

**Q: Can I use custom or fine-tuned models?**
A: Yes, LM Studio supports any GGUF format model. Convert using llama.cpp tools if needed.

**Q: What if LM Studio crashes or hangs?**
A: Restart LM Studio, check system RAM usage, try a smaller model, or reduce context length.

**Q: Is internet required after setup?**
A: No, once models are downloaded, everything runs locally without internet.

**Q: Can I run this on a server?**
A: Yes, but ensure proper security measures and consider resource requirements.

## Support

For additional help:

- **LM Studio**: Check their documentation and community forums
- **PennyGPT**: Run the test suite and check logs for specific errors  
- **Models**: Refer to model cards on Hugging Face for usage guidelines

Remember to verify your setup with the test commands provided in the "Configure PennyGPT" section above.
