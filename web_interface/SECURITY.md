# 🔒 Penny Web Interface - Security Guide

## 🛡️ Quick Answer

**By default: Only YOU on THIS COMPUTER can access Penny.**

The web interface is configured to be **localhost-only** for maximum security.

---

## 🔍 Security Levels

### **Level 1: Localhost Only** ⭐ **DEFAULT (MOST SECURE)**

**Configuration:**
```python
host='127.0.0.1'  # Localhost only
```

**Who can access:**
- ✅ You on this computer only
- ❌ No one else (even on same WiFi)
- ❌ No mobile devices
- ❌ No internet access

**How to use:**
```bash
python3 server.py
# Access at: http://localhost:5000
```

**Best for:**
- Maximum security
- Private conversations
- Sensitive work
- Default usage

---

### **Level 2: Local Network Access**

**Configuration:**
```bash
export PENNY_ALLOW_NETWORK=true
python3 server.py
```

**Who can access:**
- ✅ You on this computer
- ✅ Your phone/tablet on same WiFi
- ✅ Anyone else on your WiFi (roommates, guests)
- ❌ No one on the internet

**How to use:**
```bash
# Enable network access
export PENNY_ALLOW_NETWORK=true
python3 server.py

# On mobile (same WiFi):
# http://YOUR_IP:5000
# (Server will show your IP when starting)
```

**Best for:**
- Using Penny on mobile
- Trusted home network
- Casual conversations

**Risks:**
- Anyone on your WiFi can access
- No authentication
- Conversations visible to network users

---

### **Level 3: Internet Access** ⚠️ **NOT CONFIGURED (DON'T DO THIS)**

**Would require:**
- Port forwarding on router
- Static IP or dynamic DNS
- HTTPS/SSL certificates
- Authentication system (login)
- Rate limiting
- Security hardening

**Who could access:**
- ⚠️ ANYONE IN THE WORLD with the URL

**Status:**
- ❌ Not implemented
- ❌ Not recommended without authentication
- ❌ Security risks

**Use when:**
- Never (unless you add proper security)
- Professional deployment needed
- Want to monetize/share publicly

---

## 🎯 Recommended Usage

### **For Most Users:** ⭐

**Use localhost-only (default):**
```bash
python3 server.py
# Access: http://localhost:5000
```

**Why:**
- ✅ Maximum security
- ✅ No one else can access
- ✅ Private conversations
- ✅ No configuration needed

---

### **If You Want Mobile Access:**

**Option A: Enable Network (Less Secure)**
```bash
export PENNY_ALLOW_NETWORK=true
python3 server.py
```

**Option B: SSH Tunnel (More Secure)** ⭐ **RECOMMENDED**
```bash
# On your computer:
python3 server.py  # Localhost only

# On your phone/tablet (using SSH app):
ssh -L 5000:localhost:5000 you@your-computer-ip

# Then access: http://localhost:5000 on mobile
```

**Why Option B is better:**
- ✅ Still localhost-only on server
- ✅ Encrypted connection
- ✅ Requires SSH authentication
- ✅ No WiFi exposure

---

## 🔒 Security Best Practices

### **1. Default to Localhost** ✅
```bash
# Always start with localhost-only
python3 server.py
```

### **2. Only Enable Network When Needed** ✅
```bash
# Temporarily enable for mobile
export PENNY_ALLOW_NETWORK=true
python3 server.py

# Stop server when done
# Ctrl+C
```

### **3. Never Expose to Internet** ❌
```bash
# DON'T DO THIS:
# - Port forwarding on router
# - Public IP without authentication
# - Sharing URL publicly
```

### **4. Use Strong WiFi Password** ✅
If using network mode, ensure your WiFi has:
- WPA3 or WPA2 encryption
- Strong password
- Guest network for visitors

### **5. Monitor Access** ✅
```bash
# Server logs show all requests
# Watch for unexpected IPs
```

---

## 🚨 What Could Go Wrong?

### **Scenario 1: Network Mode + Weak WiFi**
```
Problem: Guest on WiFi accesses Penny
Risk: Sees your personality data, conversations
Solution: Use localhost-only OR secure WiFi
```

### **Scenario 2: Accidentally Port-Forwarded**
```
Problem: Router forwards port 5000 to internet
Risk: Anyone can access Penny
Solution: Check router settings, disable forwarding
```

### **Scenario 3: Public WiFi + Network Mode**
```
Problem: Coffee shop WiFi, network mode enabled
Risk: Anyone in coffee shop can access
Solution: NEVER use network mode on public WiFi
```

---

## 🛠️ How to Check Your Security

### **1. Check Current Mode:**
```bash
# Start server, look for output:

# Localhost-only (SECURE):
🔒 Security Mode: Localhost Only (Secure)
✅ Secure: Only accessible on this computer

# Network mode (LESS SECURE):
🔒 Security Mode: Network Accessible
⚠️  WARNING: Network access enabled!
```

### **2. Test from Another Device:**
```bash
# On another device on same WiFi:
curl http://YOUR_COMPUTER_IP:5000

# Localhost mode: Connection refused ✅
# Network mode: HTML returned ⚠️
```

### **3. Check Firewall:**
```bash
# macOS:
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# Ensure firewall is on for added security
```

---

## 🎯 Comparison: Security vs Convenience

| Mode | Security | Convenience | Best For |
|------|----------|-------------|----------|
| Localhost | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Most users |
| Network | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Trusted networks |
| SSH Tunnel | ⭐⭐⭐⭐⭐ | ⭐⭐ | Tech-savvy users |
| Internet | ⭐ | ⭐⭐⭐⭐⭐ | Don't do this |

---

## 💡 Advanced: Adding Authentication

If you want to enable network mode securely:

### **Option 1: Basic Auth (Quick)**
```python
# In server.py
from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

users = {
    "you": "your_password"  # Change these!
}

@auth.verify_password
def verify_password(username, password):
    if username in users:
        return users.get(username) == password
    return False

@app.route('/chat', methods=['POST'])
@auth.login_required
def chat():
    # ... existing code
```

### **Option 2: API Key (Better)**
```python
# In server.py
API_KEY = "your-secret-key-here"  # Generate securely!

@app.before_request
def check_api_key():
    if request.endpoint != 'index':
        key = request.headers.get('X-API-Key')
        if key != API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
```

### **Option 3: OAuth (Professional)**
- Implement Google/GitHub OAuth
- Use Flask-Dance or similar
- Requires more setup

---

## 🎊 Summary

### **Default Security:**
✅ **Localhost-only - Maximum security**
- Only accessible on your computer
- No network exposure
- Recommended for most users

### **To Enable Mobile:**
```bash
# Less secure (anyone on WiFi):
export PENNY_ALLOW_NETWORK=true

# More secure (SSH tunnel):
ssh -L 5000:localhost:5000 you@computer
```

### **Never Do:**
❌ Port forward without authentication
❌ Use network mode on public WiFi
❌ Share URL publicly without security

---

## 📞 Quick Reference

**Check current security:**
```bash
python3 server.py
# Look for "Security Mode" in output
```

**Enable network access:**
```bash
export PENNY_ALLOW_NETWORK=true
python3 server.py
```

**Disable network access:**
```bash
unset PENNY_ALLOW_NETWORK
python3 server.py
```

**Find your local IP:**
```bash
# macOS/Linux:
ifconfig | grep "inet "

# Windows:
ipconfig
```

---

**You're secure by default. Penny is only accessible to you.** 🔒✨
