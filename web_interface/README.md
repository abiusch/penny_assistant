# 💜 Penny Web Interface

Beautiful, easy-to-read chat interface for talking with Penny.

---

## 🎨 Features

- **Clean Chat UI** - Modern, easy-on-the-eyes design
- **Dark Mode** - Comfortable for long conversations
- **Code Highlighting** - Syntax-highlighted code blocks
- **Real-Time Personality** - See Penny's personality evolve
- **Debug Panel** - Technical insights when you need them
- **Typing Indicators** - Know when Penny is thinking
- **Smooth Animations** - Polished, professional feel

---

## 🚀 Quick Start

### **1. Install Flask (if not already installed)**
```bash
pip install flask flask-cors
```

### **2. Start the Server**
```bash
cd /Users/CJ/Desktop/penny_assistant/web_interface
python3 server.py
```

### **3. Open Your Browser**
Navigate to: **http://localhost:5000**

That's it! Start chatting with Penny.

---

## 📊 Interface Overview

### **Main Chat Area**
- **Your messages**: Blue bubbles on the right
- **Penny's responses**: Gray bubbles on the left with 💜 icon
- **Timestamps**: Show when messages were sent
- **Code blocks**: Automatically formatted and highlighted

### **Header**
- **Status**: Shows "Ready" or "Penny is thinking..."
- **Debug Info**: Toggle technical details panel
- **Clear Chat**: Start a fresh conversation

### **Footer**
- **Input Field**: Type your messages here
- **Send Button**: Or press Enter to send
- **Personality Stats**: Real-time tracking of:
  - 🎭 Formality level (0-1)
  - 🧠 Technical depth (0-1)
  - 📚 Vocabulary terms learned

### **Debug Panel** (Optional)
- **Last Response**: Full JSON data
- **Personality State**: Current dimensions & confidence
- **Console Logs**: Technical debugging info

---

## 💡 Usage Tips

### **For Coding Help:**
```
You: Can you refactor this code?
def calc(x,y): return x+y

Penny: [Shows refactored code with explanation]
```

### **For General Chat:**
```
You: What's your take on tabs vs spaces?

Penny: [Gives opinionated tech advice]
```

### **For Research:**
```
You: What's the current Python version?

Penny: [Uses web search, shows results with citations]
```

---

## 🎯 Keyboard Shortcuts

- **Enter**: Send message
- **Esc**: Clear input field
- **Ctrl+L**: Clear chat (with confirmation)

---

## 🐛 Troubleshooting

### **"Connection Error"**
**Problem**: Can't reach server
**Solution**: 
```bash
# Make sure server is running
python3 server.py

# Check it's on port 5000
curl http://localhost:5000/personality
```

### **"Module not found"**
**Problem**: Missing Python dependencies
**Solution**:
```bash
pip install flask flask-cors
```

### **Personality Not Updating**
**Problem**: Stats show "--"
**Solution**:
- Give it a few conversations to build confidence
- Check `data/personality_tracking.db` exists
- Restart server if needed

### **Slow Responses**
**Problem**: Takes a while to respond
**Solution**:
- Normal for first message (loads models)
- If consistently slow, check GPT-OSS is running
- Debug panel shows timing info

---

## 🔧 Configuration

### **Change Port**
Edit `server.py`:
```python
app.run(host='0.0.0.0', port=5000, debug=True)
                         # ^^^^ Change this
```

### **Enable HTTPS** (Advanced)
For production use with SSL:
```python
app.run(host='0.0.0.0', port=5000, 
        ssl_context=('cert.pem', 'key.pem'))
```

### **Customize Colors**
Edit `index.html`, change Tailwind colors:
```html
<!-- Penny's messages -->
bg-gray-800  → bg-purple-900

<!-- Your messages -->
bg-blue-600  → bg-green-600

<!-- Accent color -->
bg-purple-600 → bg-pink-600
```

---

## 📱 Mobile Support

The interface is responsive and works on:
- ✅ Desktop (Chrome, Firefox, Safari, Edge)
- ✅ Tablets (iPad, Android tablets)
- ✅ Mobile phones (iOS, Android)

**Mobile Tips:**
- Tap input field to start typing
- Swipe to scroll chat history
- Landscape mode recommended for code

---

## 🎨 Screenshots

### **Main Chat**
```
┌─────────────────────────────────────┐
│  💜 Penny Assistant          [Debug]│
│  Ready                       [Clear]│
├─────────────────────────────────────┤
│                                      │
│     You: Can you help with code?    │
│     2:34 PM                          │
│                                      │
│  💜 Penny: Sure, what's the code?   │
│  2:34 PM                             │
│                                      │
├─────────────────────────────────────┤
│  Type your message...        [Send] │
│  🎭 0.40 | 🧠 0.50 | 📚 59          │
└─────────────────────────────────────┘
```

### **Debug Panel**
```
┌─────────────────────────────────┐
│  Debug Info                  [×]│
├─────────────────────────────────┤
│  Last Response                   │
│  {                               │
│    "response": "...",            │
│    "metadata": {...}             │
│  }                               │
│                                  │
│  Personality State               │
│  {                               │
│    "formality": 0.40,            │
│    "technical_depth": 0.50       │
│  }                               │
│                                  │
│  Console Logs                    │
│  [2:34 PM] Research: False       │
│  [2:35 PM] Adjustments: none     │
└─────────────────────────────────┘
```

---

## 🚀 Next Steps

### **Current (Works Now)**
- ✅ Chat with Penny via web interface
- ✅ See personality stats in real-time
- ✅ Debug panel for development
- ✅ Code syntax highlighting

### **Coming Soon (Easy Additions)**
- [ ] Message editing
- [ ] Conversation history save/load
- [ ] Export chat to markdown
- [ ] Voice input (browser speech recognition)
- [ ] Dark/light theme toggle
- [ ] Customizable colors

### **Future (More Complex)**
- [ ] Multi-user support (login)
- [ ] Mobile app version
- [ ] Conversation search
- [ ] Analytics dashboard

---

## 📝 Technical Details

### **Stack**
- **Frontend**: HTML + Tailwind CSS + Vanilla JS
- **Backend**: Flask (Python)
- **API**: REST (JSON)
- **State**: In-memory (server restarts clear state)

### **API Endpoints**

**POST /chat**
```json
{
  "message": "Your message here"
}
```

**Response:**
```json
{
  "response": "Penny's response",
  "metadata": {
    "research": false,
    "adjustments": []
  },
  "personality": {
    "formality": "0.40",
    "technical_depth": "0.50",
    "vocabulary_count": 59
  }
}
```

**GET /personality**
```json
{
  "formality": "0.40",
  "technical_depth": "0.50",
  "vocabulary_count": 59,
  "confidence": "0.30"
}
```

---

## 💡 Comparison: Terminal vs Web

| Feature | Terminal | Web Interface |
|---------|----------|---------------|
| Ease of Use | ⚠️ Technical | ✅ Friendly |
| Readability | ⚠️ Basic | ✅ Beautiful |
| Code Display | ⚠️ Plain text | ✅ Highlighted |
| Personality Visible | ❌ No | ✅ Yes |
| Debug Info | ✅ Always on | ✅ Toggle |
| Mobile Support | ❌ No | ✅ Yes |
| Accessibility | ⚠️ Limited | ✅ Good |

**Recommendation:** Use web interface for daily chatting, terminal for debugging/development.

---

## 🎉 Enjoy!

You now have a beautiful, easy-to-read interface for Penny.

**Questions?** Check the main Penny README or raise an issue.

**Tips?** The web interface makes long conversations much more pleasant. Give it a try!

---

**Made with 💜 for Penny Assistant**
