# ChatGPT MCP Connector Setup Instructions

## The Issue You're Seeing

The ChatGPT connector form is asking for an HTTP URL (`http://localhost:8000`), but **MCP servers don't work that way**. ChatGPT expects to **launch a command directly**, not connect to a running HTTP server.

## Correct Setup for ChatGPT

### Step 1: Use the Command, Not URL

In the ChatGPT connector form:

**❌ Don't use:** `http://localhost:8000`  
**✅ Use this instead:**

- **MCP Server URL:** `python3 /Users/CJ/Desktop/penny_assistant/mcp_chatgpt_connector.py`
- **Authentication:** No authentication

### Step 2: Alternative - Use stdio Protocol

Or create a script that ChatGPT can execute:

1. **Name:** `ChatGPT Connector`
2. **Description:** `Connects to ChatGPT API for cross-AI communication`
3. **MCP Server URL:** `python3 /Users/CJ/Desktop/penny_assistant/mcp_chatgpt_connector.py`
4. **Authentication:** No authentication

### Step 3: Environment Variables

Make sure your OpenAI API key is set:
```bash
export OPENAI_API_KEY="your-actual-openai-api-key"
```

## How MCP Actually Works

MCP (Model Context Protocol) works by:
1. ChatGPT **launches your Python script** as a subprocess
2. Communicates via **stdin/stdout** (not HTTP)
3. Uses JSON-RPC protocol over stdio

## Test the MCP Server

Before connecting to ChatGPT, test it works:
```bash
export OPENAI_API_KEY="your-key"
python3 mcp_chatgpt_connector.py
```

## What You Should See

When ChatGPT launches your connector, you'll have access to:
- `ask_chatgpt` - Send messages to ChatGPT
- `chatgpt_conversation` - Multi-turn conversations  
- `compare_responses` - Compare AI responses
- Resources for models and conversation history

The key insight: **MCP is not HTTP** - it's a subprocess communication protocol!
