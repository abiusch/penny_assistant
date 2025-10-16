# 🔧 Task for Claude Code: Restore Correct Server Implementation

## 🎯 What Needs to be Done

The `web_interface/server.py` file currently has **incorrect imports and methods** that were accidentally introduced. Please restore the correct implementation that was previously working.

---

## ✅ Correct Implementation (What It Should Be)

### **Correct Imports:**
```python
from research_first_pipeline import ResearchFirstPipeline
from personality_tracker import PersonalityTracker  # ✅ Root level, not src.personality
```

### **Correct API Method:**
```python
from core.pipeline import State

@app.route('/chat', methods=['POST'])
def chat():
    # ... setup code ...
    
    # ✅ CORRECT: Use state machine + think()
    pipeline.state = State.THINKING
    response_text = pipeline.think(user_message)
    
    # NOT: pipeline.process_message() - this method doesn't exist
    # NOT: asyncio.run(...) - think() is synchronous
```

---

## 🔍 What You Previously Fixed (Reference)

From your `WEB_INTERFACE_IMPLEMENTATION_SUMMARY.md`:

**Issue 2: Wrong Import Path**
- **Wrong:** `from src.personality.personality_tracker import PersonalityTracker`
- **Right:** `from personality_tracker import PersonalityTracker`
- **Reason:** File is at project root, not in src/personality/

**Issue 3: API Method Mismatch**
- **Wrong:** `response = await pipeline.process_message(user_message)`
- **Right:** 
  ```python
  from core.pipeline import State
  pipeline.state = State.THINKING
  response_text = pipeline.think(user_message)
  ```
- **Reason:** ResearchFirstPipeline uses state machine with `think()` method

---

## 📝 Full Correct Implementation

```python
#!/usr/bin/env python3
"""
Penny Web Interface - Flask Backend
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from research_first_pipeline import ResearchFirstPipeline
from personality_tracker import PersonalityTracker  # ✅ Correct path
from core.pipeline import State  # ✅ For state machine

app = Flask(__name__, static_folder='.')
CORS(app)

# Security configuration
ALLOW_NETWORK = os.environ.get('PENNY_ALLOW_NETWORK', 'False').lower() == 'true'

# Initialize Penny
print("Initializing Penny's pipeline...")
pipeline = ResearchFirstPipeline()
personality_tracker = PersonalityTracker()
print("✅ Penny initialized successfully!")

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        print(f"\n📝 User: {user_message}")
        
        # ✅ CORRECT: Use state machine
        pipeline.state = State.THINKING
        response_text = pipeline.think(user_message)
        
        print(f"🤖 Penny: {response_text[:100]}...")
        
        # Extract metadata
        metadata = {
            'research': False,  # TODO: Extract from pipeline
            'adjustments': [],  # TODO: Extract from pipeline
        }
        
        # Get personality info
        personality = get_personality_info()
        
        return jsonify({
            'response': response_text,
            'metadata': metadata,
            'personality': personality
        })
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/personality', methods=['GET'])
def personality():
    try:
        info = get_personality_info()
        return jsonify(info)
    except Exception as e:
        print(f"Error getting personality info: {e}")
        return jsonify({'error': str(e)}), 500

def get_personality_info():
    # ... existing implementation ...
    pass

if __name__ == '__main__':
    host = '0.0.0.0' if ALLOW_NETWORK else '127.0.0.1'
    security_mode = "Network Accessible" if ALLOW_NETWORK else "Localhost Only (Secure)"
    
    print("=" * 60)
    print("🤖 Penny Web Interface Starting...")
    print(f"🔒 Security Mode: {security_mode}")
    print("📱 Open your browser to: http://localhost:5001")
    print("=" * 60)
    
    app.run(host=host, port=5001, debug=False)
```

---

## 🎯 Why This Is Correct

1. **PersonalityTracker is at root level** - Not in src/personality/
2. **ResearchFirstPipeline uses state machine** - Requires State.THINKING before think()
3. **think() is synchronous** - No asyncio.run() needed
4. **Port 5001** - Avoids macOS AirPlay on 5000

---

## ✅ After Fixing

The server should:
- Start without import errors
- Connect to Penny's actual pipeline
- Process messages through Phase 1+2 personality system
- Show console output: "🎭 Personality-enhanced prompt applied"
- Show console output: "🎨 Response post-processed"

---

## 🔍 How to Test

```bash
# Start server
cd /Users/CJ/Desktop/penny_assistant/web_interface
python3 server.py

# In another terminal, test:
curl -X POST http://localhost:5001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "hi"}'

# Should see proper Penny response with personality system active
```

---

## 📚 Reference

See `WEB_INTERFACE_IMPLEMENTATION_SUMMARY.md` for full context of previous fixes.

---

**Priority:** High - Server currently has broken implementation
**Estimated Time:** 5-10 minutes
**Files to Modify:** `web_interface/server.py`
