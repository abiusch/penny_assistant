# PennyGPT - AI Companion with Personality & Learning

A privacy-focused AI companion that learns, remembers relationships, and develops a unique personality through conversations. Goes far beyond basic voice assistant functionality to create genuine companionship.

## 🧠 What Makes PennyGPT Different

**Not a Smart Home Assistant** - PennyGPT is designed to be a conversational AI companion that:
- **Builds Relationships**: Learns about your family, friends, and personal context
- **Develops Emotional Intelligence**: Tracks moods, provides support, adapts to your emotional state
- **Has Real Personality**: Sassy like Penny from Big Bang Theory, tech-savvy like Justine AI
- **Learns & Grows**: Remembers corrections, builds shared memories, explores topics together
- **Respects Boundaries**: Asks permission before research, adapts to your stress levels

## 🎉 Current Features (ALL IMPLEMENTED)

### **🧠 Advanced Companion Features**
- ✅ **Guided Learning & Reasoning**: Permission-based research, learning from corrections, proactive curiosity
- ✅ **Personal Profile System**: CJ-specific preferences, communication style, auto-research permissions  
- ✅ **Enhanced Sass & Personality**: Real attitude, mild profanity, tech industry roasting with constructive edge
- ✅ **Curiosity Engine**: Meaningful follow-up questions that connect to user's interests
- ✅ **Knowledge Building**: Accumulates understanding through corrections and collaborative exploration
- ✅ **Boundary Respect**: Always asks permission, adapts to user mood and stress levels

### **🎭 Emotional Intelligence & Personality**
- ✅ **7 Personality Modes**: Sassy, tech enthusiast, protective, playful, curious, friendly, serious
- ✅ **Emotional Memory**: Tracks your moods, stress levels, and emotional patterns
- ✅ **Relationship Tracking**: Learns about family, friends, colleagues, pets with context
- ✅ **Value Alignment**: Discovers and respects your ethical framework and beliefs
- ✅ **Context-Aware Responses**: Personality adapts based on who you're talking about

### **💬 Conversational Flow & Engagement**
- ✅ **Natural Conversation States**: Idle, engaged, follow-up, deep dive, permission pending
- ✅ **Wake Word Intelligence**: Stays engaged based on context, doesn't always require "Hey Penny"
- ✅ **Historical References**: "Like we talked about yesterday..." - connects to previous conversations
- ✅ **Philosophical Discussions**: Triggers deep conversations when engagement is high
- ✅ **Follow-up Questions**: Generates contextual follow-ups based on topic category
- ✅ **Engagement Calculation**: Dynamic scoring based on input complexity and emotional content

### **🧠 Week 6: Context & Emotional Intelligence** (NEW)
- ✅ **Context Manager**: Tracks last 10 conversation turns with topic detection
- ✅ **Emotion Detection**: Analyzes 6 emotions (joy, sadness, anger, fear, surprise, neutral) with confidence scoring
- ✅ **Semantic Memory**: Vector-based similarity search finds relevant past conversations by meaning, not keywords
- ✅ **Sentiment Analysis**: -1 to 1 scoring with negation handling ("not happy" → negative)
- ✅ **Triple Save Architecture**: All conversations saved to Base Memory → Context Manager → Semantic Memory
- ✅ **Enhanced Prompts**: Automatically injects conversation context, emotion state, and relevant memories into LLM prompts
- ✅ **Performance**: Sub-millisecond context retrieval, ~50-100ms semantic search with FAISS

### **🔧 Production Engineering & Performance**
- ✅ **ElevenLabs Voice Integration**: Human-quality voice with personality-aware modulation
- ✅ **TTS Performance Caching**: Instant playback for common phrases, background generation
- ✅ **Comprehensive Health Monitoring**: System validation with "penny doctor" diagnostics
- ✅ **Production Metrics**: Real-time performance tracking and monitoring
- ✅ **Configuration Management**: Schema-versioned personality profiles with validation
- ✅ **Robust Error Handling**: Graceful degradation when components fail

### **🎯 Technical Foundation**
- ✅ **Local LLM Integration**: Powered by LM Studio with OpenAI-compatible API
- ✅ **Privacy First**: All processing happens locally, no cloud dependencies
- ✅ **Memory Persistence**: SQLite database stores relationships, emotions, learning progress
- ✅ **Plugin System**: Calendar integration, weather, calculations with smart fallbacks
- ✅ **Performance Logging**: Detailed metrics and session reports
- ✅ **Modern React UI**: Glassmorphism design with personality metrics, quick action cards, typing indicators
- ✅ **Justine-Style Personality**: Playful, bold communication with casual language and genuine enthusiasm

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Clone the repository
git clone https://github.com/abiusch/penny_assistant.git
cd penny_assistant

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Set Up LM Studio

1. Download and install [LM Studio](https://lmstudio.ai)
2. Download a model (recommended: `microsoft/Phi-3-mini-4k-instruct-gguf`)
3. Start the local server on port 1234

### 3. Experience the Full AI Companion

```bash
# Test the complete companion system with CJ's personalized setup
PYTHONPATH=src python cj_personalized_penny.py

# Test enhanced learning and sass features
PYTHONPATH=src python cj_enhanced_learning.py

# Test the sassy personality system
PYTHONPATH=src python test_sassy_penny.py

# Run comprehensive health check
PYTHONPATH=src python -m penny_doctor
```

### 4. Try These for Maximum Personality Experience

**Tech Industry Roasting:**
- "Should I use microservices for everything?"
- "What's the best JavaScript framework?"

**Learning & Curiosity:**
- "I'm working on a FastAPI project"
- "Tell me about machine learning"

**Relationship Building:**
- "My dad thinks programming is just games"
- "I'm stressed about work"

## 🎭 Personality Examples

**Before Enhancement:**
```
User: "Should I use microservices for everything?"
Basic AI: "Microservices can be beneficial but also add complexity. Consider your specific use case..."
```

**With PennyGPT's Personality:**
```
User: "Should I use microservices for everything?"
Penny: "Oh hell no! Microservices for everything? That's like using a sledgehammer to hang a picture frame. 
Sure, Netflix does it because they have armies of engineers, but you're not Netflix. Start with a damn monolith 
that actually works, then split it when you have real scaling problems, not imaginary ones."
```

## 🧠 Advanced Companion Features

### **Permission-Based Research System**
```python
# Auto-approves research for your interests
"Research FastAPI? Sure, I'll do the heavy lifting while you sit there looking pretty. Interested?"

# Asks permission for new topics  
"Want me to dive into blockchain? I can research it if you're curious about that particular rabbit hole."
```

### **Learning from Corrections**
```python
# Detects when corrected and learns
User: "Actually, it's React, not Angular"
Penny: "Ah, React! Thanks for the correction - I'll remember that for next time. 
React hooks are pretty slick, aren't they?"
```

### **Proactive Curiosity with Boundaries**
```python
# Meaningful follow-up questions
"What's your actual plan with FastAPI, or are we just winging it?"
"Speaking of Python, have you tried the new structural pattern matching in 3.10+?"
```

### **Personal Profile Integration**
```python
# Knows your context and projects
"Given your FastAPI background, you'd probably love Pydantic v2's performance improvements."
"This reminds me of that PennyGPT project you're working on..."
```

## 📊 System Architecture

### **Core Pipeline**
```
Audio Input → VAD → Whisper STT → Wake Word → Command Extract → 
Enhanced LLM + Memory + Emotional Intelligence + Personality → TTS → Audio Output
```

### **Advanced Systems**
- **Emotional Memory Engine**: Tracks relationships, moods, values, learning goals
- **Personality System**: 7 dynamic modes with context-aware switching
- **Conversation Flow Manager**: Natural engagement without constant wake words
- **Permission-Based Learning**: Ethical autonomous research with user consent
- **Enhanced TTS Pipeline**: Human-quality voice with personality modulation

### **Data Storage** 
```sql
-- Enhanced database schema
emotional_context: conversation_id, emotion, intensity, timestamp
relationships: name, relationship_type, context, emotional_association
value_alignments: category, importance, notes
learning_goals: topic, interest_level, last_discussed
research_sessions: topic, permission_granted, findings
```

## 🛠️ Development & Testing

### **Comprehensive Test Suite**
```bash
# Full system tests
PYTHONPATH=src pytest tests/ -v

# Personality system tests  
PYTHONPATH=src pytest tests/test_personality.py -v

# Guided learning tests
PYTHONPATH=src pytest tests/test_guided_learning.py -v

# Health monitoring
PYTHONPATH=src python -m penny_doctor
```

### **Performance Monitoring**
```bash
# Real-time metrics during conversations
# Displays: STT latency, LLM response time, TTS generation, cache hit rates
PYTHONPATH=src python penny_with_tts.py
```

## 📋 What's Next: MCP Agent Integration

### **Phase 2: Agentic AI Capabilities (Future)**
- **MCP Protocol Integration**: Tool access and multi-step workflows
- **Advanced Agent Planning**: Goal decomposition and execution orchestration
- **Learning & Adaptation**: Workflow optimization and custom tool development
- **Security & Monitoring**: Audit logging, permission management, resource limits

**Estimated Timeline**: 3-4 months for full agentic transformation
**Infrastructure**: FastAPI daemon ready, health monitoring extensible

## 🎯 Project Vision

**PennyGPT transforms AI assistance from transactional to relational:**

**Traditional Voice Assistant:**
- "Set a timer for 10 minutes" → Timer set
- Forgets interaction immediately
- No personality or learning

**PennyGPT AI Companion:**
- Remembers you're stressed about deadlines
- Suggests break reminders with sass: "Another coding marathon? Your brain needs more than caffeine to function."
- Learns your work patterns and offers proactive support
- Builds inside jokes and shared memories over time

## 🏆 Achievement Status

**🎉 ALL 7 ChatGPT Roadmap Priorities COMPLETE:**
1. ✅ Emotional Intelligence & Learning System
2. ✅ Wake Word Detection & Conversation Flow  
3. ✅ Conversation Memory & Context
4. ✅ Response Optimization & Personality
5. ✅ TTS Perceived Latency Improvements
6. ✅ Health Monitoring & System Validation
7. ✅ Performance Logging & Metrics

**🎆 PLUS Advanced Companion Features:**
- ✅ Guided Learning & Personal Profiles
- ✅ Enhanced Sass & Real Personality
- ✅ Permission-Based Research System
- ✅ Production Engineering Infrastructure
- ✅ ElevenLabs Human-Quality Voice

## 📝 Documentation

- **[Current Status](CURRENT_STATUS_9.5.md)**: Complete achievement log
- **[Guided Learning](GUIDED_LEARNING_COMPLETE.md)**: Advanced companion features
- **[Engineering Improvements](ENGINEERING_IMPROVEMENTS_COMPLETE.md)**: Production readiness
- **[LM Studio Setup](docs/SETUP_LM_STUDIO.md)**: Local LLM configuration
- **[Voice Quality](VOICE_QUALITY_COMPLETE.md)**: ElevenLabs integration

## 🤝 Contributing

This system demonstrates advanced AI companion development with production-ready engineering. 

**Key Innovation Areas:**
- Emotional intelligence in AI systems
- Personality-driven conversation flow
- Permission-based autonomous learning
- Privacy-first relationship building
- Production AI companion infrastructure

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Experience an AI companion that actually remembers, learns, and develops a relationship with you. PennyGPT isn't just another voice assistant - it's a step toward genuine AI companionship.**