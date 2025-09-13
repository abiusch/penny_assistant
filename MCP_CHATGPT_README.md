# MCP ChatGPT Connector

A Model Context Protocol (MCP) server that connects GitHub Copilot to ChatGPT, allowing seamless communication between AI systems.

## Features

🔗 **Direct ChatGPT Integration**
- Send messages to ChatGPT from GitHub Copilot
- Multi-turn conversation support
- Model selection (GPT-4, GPT-3.5-turbo, etc.)
- Customizable parameters (temperature, max_tokens)

🔄 **AI Comparison Tools**
- Compare responses between GitHub Copilot and ChatGPT
- Side-by-side analysis capabilities
- Context preservation across systems

📊 **Resource Management**
- Available ChatGPT models listing
- Conversation history tracking
- Usage statistics

## Setup Instructions

### 1. Install Dependencies
```bash
pip install mcp httpx
```

### 2. Set OpenAI API Key
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

Or update the `mcp_config.json` file with your API key.

### 3. Run the MCP Server
```bash
python3 mcp_chatgpt_connector.py
```

### 4. Connect via MCP Client
Use the configuration in `mcp_config.json` to connect your MCP client to this server.

## Available Tools

### `ask_chatgpt`
Send a single message to ChatGPT and get a response.

**Parameters:**
- `message` (required): The message to send
- `model` (optional): ChatGPT model to use (default: gpt-4)
- `system_prompt` (optional): System prompt for behavior
- `temperature` (optional): Creativity level (0.0-2.0)
- `max_tokens` (optional): Maximum response length

**Example:**
```json
{
  "message": "Explain quantum computing in simple terms",
  "model": "gpt-4",
  "temperature": 0.7
}
```

### `chatgpt_conversation`
Have a multi-turn conversation with ChatGPT.

**Parameters:**
- `messages` (required): Array of conversation messages
- `model` (optional): ChatGPT model to use

**Example:**
```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful programming assistant"},
    {"role": "user", "content": "How do I implement a binary search?"},
    {"role": "assistant", "content": "Here's how to implement binary search..."},
    {"role": "user", "content": "Can you show me the Python code?"}
  ]
}
```

### `compare_responses`
Get responses from both GitHub Copilot context and ChatGPT for comparison.

**Parameters:**
- `question` (required): Question to ask both systems
- `copilot_context` (optional): Current Copilot context

## Available Resources

### `chatgpt://models`
Lists available ChatGPT models and their descriptions.

### `chatgpt://conversation-history`
Access to recent conversation history (implementation specific).

## Use Cases

1. **Cross-AI Consultation**: Get second opinions from ChatGPT on Copilot suggestions
2. **Response Comparison**: Compare different AI approaches to the same problem
3. **Extended Conversations**: Continue conversations across different AI systems
4. **Model Experimentation**: Test different ChatGPT models for specific tasks

## Security Notes

- Keep your OpenAI API key secure
- The connector is in BETA - intended for developer use only
- Review all API calls and responses for sensitive information

## Integration with Penny Assistant

This connector can be integrated with your Penny Assistant project to:
- Get ChatGPT's perspective on technical decisions
- Compare Penny's responses with ChatGPT
- Use ChatGPT as a fallback for specific queries
- Enhance Penny's knowledge base with ChatGPT insights
