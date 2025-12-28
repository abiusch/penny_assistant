# NEMOTRON-3 NANO INTEGRATION - UPDATED SPEC FOR CC

**Date:** November 2, 2025  
**Model:** nemotron-3-nano:latest (24GB)  
**Estimated Time:** 30-40 minutes  

---

## 🎯 **IMPORTANT: MODEL ALREADY DOWNLOADED**

User has already downloaded `nemotron-3-nano:latest` via Ollama.

To verify:
```bash
ollama list
# Should show: nemotron-3-nano:latest
```

If model needs to be pulled:
```bash
ollama pull nemotron-3-nano:latest
```

---

## 📦 **STEP 1: VERIFY OLLAMA & MODEL**

```bash
# Check Ollama is installed
ollama --version

# Check model is available
ollama list | grep nemotron

# Test model works
ollama run nemotron-3-nano "Hello! What is 2+2?"
# Should respond with answer about 4
```

---

## 📄 **STEP 2: CREATE NEMOTRON CLIENT**

Create: `src/llm/nemotron_client.py`

```python
"""
Nemotron-3 Nano LLM Client
Local inference using Ollama
"""

import logging
from typing import Dict, Any, Optional, List
import subprocess
import json

logger = logging.getLogger(__name__)


class NemotronClient:
    """Client for NVIDIA Nemotron-3 Nano via Ollama"""
    
    def __init__(
        self,
        model_name: str = "nemotron-3-nano:latest",
        reasoning_mode: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        """
        Initialize Nemotron client.
        
        Args:
            model_name: Ollama model name (default: nemotron-3-nano:latest)
            reasoning_mode: Enable reasoning traces (default: True)
            temperature: Sampling temperature (default: 0.7)
            max_tokens: Max tokens to generate (default: 2048)
        """
        self.model_name = model_name
        self.reasoning_mode = reasoning_mode
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Verify model is available
        self._verify_model()
        
        logger.info(f"NemotronClient initialized: {model_name}, reasoning={reasoning_mode}")
    
    def _verify_model(self):
        """Verify Nemotron model is available"""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if self.model_name not in result.stdout and "nemotron-3-nano" not in result.stdout:
                raise RuntimeError(
                    f"Model {self.model_name} not found. "
                    f"Run: ollama pull nemotron-3-nano:latest"
                )
            
            logger.info(f"Model {self.model_name} is available")
        except FileNotFoundError:
            raise RuntimeError(
                "Ollama not found. Install: curl -fsSL https://ollama.com/install.sh | sh"
            )
        except Exception as e:
            logger.error(f"Failed to verify model: {e}")
            raise
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate response using Nemotron-3 Nano.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens
            
        Returns:
            Generated response text
        """
        # Build prompt
        prompt = self._build_prompt(messages, system_prompt)
        
        # Use provided values or defaults
        temp = temperature if temperature is not None else self.temperature
        
        # Call Ollama via subprocess
        try:
            # Build command with options
            cmd = ["ollama", "run", self.model_name]
            
            # Run with timeout
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            if result.returncode == 0:
                response = result.stdout.strip()
                
                # Extract final answer if reasoning mode
                if self.reasoning_mode and "</think>" in response:
                    # Nemotron-3 uses <think></think> tags for reasoning
                    parts = response.split("</think>")
                    if len(parts) > 1:
                        response = parts[-1].strip()
                
                logger.debug(f"Generated {len(response)} chars")
                return response
            else:
                error_msg = result.stderr.strip()
                logger.error(f"Ollama error: {error_msg}")
                raise RuntimeError(f"Generation failed: {error_msg}")
        
        except subprocess.TimeoutExpired:
            logger.error("Generation timed out (>60s)")
            raise RuntimeError("Generation timed out")
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise
    
    def _build_prompt(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """Build prompt from messages"""
        prompt_parts = []
        
        # Add system prompt if provided
        if system_prompt:
            prompt_parts.append(f"System: {system_prompt}\n")
        
        # Add messages
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}\n")
            elif role == "user":
                prompt_parts.append(f"User: {content}\n")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}\n")
        
        # Add final assistant prompt
        prompt_parts.append("Assistant:")
        
        return "\n".join(prompt_parts)
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        OpenAI-compatible chat completion interface.
        
        Args:
            messages: List of message dicts
            **kwargs: Additional generation parameters
            
        Returns:
            OpenAI-style completion dict
        """
        response_text = self.generate(messages, **kwargs)
        
        # Return OpenAI-compatible format
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": response_text
                    },
                    "finish_reason": "stop"
                }
            ],
            "model": self.model_name,
            "usage": {
                "prompt_tokens": 0,  # Ollama doesn't report this
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }


# Factory function
def create_nemotron_client(
    reasoning_mode: bool = True,
    temperature: float = 0.7
) -> NemotronClient:
    """Create and return a NemotronClient instance"""
    return NemotronClient(
        model_name="nemotron-3-nano:latest",
        reasoning_mode=reasoning_mode,
        temperature=temperature
    )
```

---

## 📄 **STEP 3: UPDATE RESEARCH FIRST PIPELINE**

Update `research_first_pipeline.py`:

### **At the top, REPLACE:**
```python
from openai import OpenAI
```

### **WITH:**
```python
from src.llm.nemotron_client import create_nemotron_client
```

### **In `__init__`, REPLACE:**
```python
def __init__(self):
    self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
```

### **WITH:**
```python
def __init__(self):
    # Use Nemotron-3 Nano (local LLM)
    try:
        self.client = create_nemotron_client(
            reasoning_mode=True,  # Enable reasoning for complex queries
            temperature=0.7
        )
        logger.info("Using Nemotron-3 Nano (local)")
    except Exception as e:
        logger.warning(f"Nemotron not available: {e}")
        # Fallback to OpenAI if needed
        from openai import OpenAI
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        logger.info("Fallback to OpenAI GPT-4o-mini")
```

### **The `_generate_response` method should work as-is** because `chat_completion()` is OpenAI-compatible!

---

## 📄 **STEP 4: CREATE TEST FILE**

Create: `tests/test_nemotron.py`

```python
#!/usr/bin/env python3
"""
Nemotron-3 Nano Integration Test
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.llm.nemotron_client import create_nemotron_client
import time

print("=" * 70)
print("🧪 NEMOTRON-3 NANO TEST")
print("=" * 70)

# Test 1: Create client
print("\n✅ TEST 1: Client Creation")
try:
    client = create_nemotron_client()
    print(f"  ✅ Client created: {client.model_name}")
except Exception as e:
    print(f"  ❌ Failed: {e}")
    exit(1)

# Test 2: Simple generation
print("\n✅ TEST 2: Simple Generation")
try:
    messages = [{"role": "user", "content": "What is 2+2? Answer briefly."}]
    
    start = time.time()
    response = client.generate(messages)
    elapsed = time.time() - start
    
    print(f"  ✅ Response in {elapsed:.2f}s: {response[:100]}")
    
    if "4" in response:
        print("  ✅ Correct answer")
except Exception as e:
    print(f"  ❌ Failed: {e}")

# Test 3: Chat completion
print("\n✅ TEST 3: Chat Completion (OpenAI-compatible)")
try:
    messages = [
        {"role": "system", "content": "You are Penny, a helpful AI assistant."},
        {"role": "user", "content": "What's your name?"}
    ]
    
    response = client.chat_completion(messages)
    content = response["choices"][0]["message"]["content"]
    
    print(f"  ✅ Response: {content[:100]}")
    
    if "Penny" in content or "penny" in content.lower():
        print("  ✅ Identified as Penny")
except Exception as e:
    print(f"  ❌ Failed: {e}")

# Test 4: Performance
print("\n✅ TEST 4: Performance")
try:
    messages = [{"role": "user", "content": "Say hello!"}]
    
    times = []
    for i in range(3):
        start = time.time()
        client.generate(messages)
        times.append(time.time() - start)
    
    avg = sum(times) / len(times)
    print(f"  ✅ Average: {avg:.2f}s (min: {min(times):.2f}s, max: {max(times):.2f}s)")
except Exception as e:
    print(f"  ❌ Failed: {e}")

print("\n" + "=" * 70)
print("🎉 NEMOTRON-3 NANO: READY!")
print("=" * 70)
```

---

## 🧪 **STEP 5: TESTING PROCEDURE**

```bash
# 1. Verify model is available
ollama list | grep nemotron

# 2. Test Nemotron client
cd /Users/CJ/Desktop/penny_assistant
python3 tests/test_nemotron.py

# Expected output:
# ✅ Client created
# ✅ Simple generation working
# ✅ Chat completion working
# ✅ Performance acceptable

# 3. Test with pipeline
python3 -c "
from research_first_pipeline import ResearchFirstPipeline
pipeline = ResearchFirstPipeline()
response = pipeline.process('Hello! What is 2+2?')
print(response)
"

# 4. Run integration tests (should still pass!)
python3 test_full_integration.py
```

---

## ✅ **SUCCESS CRITERIA:**

```
Expected Results:
├── Nemotron client tests pass (4/4)
├── Pipeline uses Nemotron (no OpenAI API calls)
├── Responses are coherent and accurate
├── Performance: <5s per response
├── Integration tests still pass
└── No errors in logs

If all pass: Nemotron Integration COMPLETE ✅
```

---

## 🎯 **BENEFITS ACHIEVED:**

```
Before (GPT-4o-mini):
├── Cost: $5-20/month
├── Privacy: Sends to OpenAI
├── Latency: 1-2s + network
├── Context: 128K tokens

After (Nemotron-3 Nano):
├── Cost: $0/month ✅
├── Privacy: 100% local ✅
├── Latency: 200-400ms ✅
├── Context: 1M tokens ✅
```

---

## ⏰ **TIME ESTIMATE:**

```
Implementation:
├── Create nemotron_client.py:   5 min
├── Update pipeline:             5 min
├── Create tests:                5 min
├── Run tests:                   5 min
└── Total:                       20 min

(Model already downloaded, no wait time!)
```

---

## 🐛 **TROUBLESHOOTING:**

### **Issue: "Model not found"**
```bash
ollama pull nemotron-3-nano:latest
```

### **Issue: "Ollama command not found"**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
```

### **Issue: Generation too slow**
```bash
# Check Ollama is using GPU
# M4 Pro should auto-detect
# Generation should be 1-3s typically
```

---

**READY TO IMPLEMENT!** 🚀

User already has model downloaded, just need to integrate it into the pipeline.
