#!/bin/bash

# 0. Ensure we're in the correct directory
cd ~/Desktop/penny_assistant

# 1. Create core directory if it doesn't exist
mkdir -p src/core

# 2. Move intent_router.py into core (with backup)
if [ -f "intent_router.py" ]; then
    cp intent_router.py src/core/intent_router.py
    mv intent_router.py intent_router.py.bak
fi

# 3. Backup main.py before removing (since it's handled by penny.py)
if [ -f "main.py" ]; then
    mv main.py main.py.bak
fi

# 4. Setup personality module
rm -rf src/personality 2>/dev/null
touch src/core/personality.py

# 5. Create LLM files (if they don't exist)
touch src/core/llm_huggingface.py
touch src/core/llm_openai.py
touch src/core/llm_manager.py

# 6. Create Phase 1.5 upgrade utilities
touch src/config.py
touch src/logger.py
touch src/validate_env.py

# 7. Create .gitignore if missing
if [ ! -f ".gitignore" ]; then
cat <<EOL > .gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
*.log

# Env
.venv/
venv/
.env
.env.*

# VS Code
.vscode/

# Jupyter
*.ipynb_checkpoints

# Ollama (optional)
~/.ollama

# Backups
*.bak
EOL
fi

# 8. Create tests folder and starter files
mkdir -p tests
touch tests/test_llm_routing.py
touch tests/test_personality.py

# 9. Ensure .vscode/settings.json exists with correct settings
mkdir -p .vscode
cat <<EOL > .vscode/settings.json
{
    "python.envFile": "\${workspaceFolder}/.env",
    "python.defaultInterpreterPath": "\${workspaceFolder}/.venv/bin/python3",
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.nosetestsEnabled": false,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "editor.formatOnSave": true,
    "python.formatting.provider": "black"
}
EOL

# 10. Clean up duplicate venv if both exist
if [ -d "venv" ] && [ -d ".venv" ]; then
    echo "Found both venv and .venv directories. Keeping .venv..."
    rm -rf venv
fi

echo "✅ PennyGPT folder structure cleaned and upgraded for Phase 1.5"
