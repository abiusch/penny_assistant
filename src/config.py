"""
Configuration settings for PennyGPT's LLM providers.
"""

import os
from typing import Dict, Any

MODEL_CONFIGS: Dict[str, Dict[str, Any]] = {
    "local": {
        "model_name": "llama2",
        "temperature": 0.7,
        "max_tokens": 1000,
    },
    "openai": {
        "model_name": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 1000,
        "api_key": os.getenv("OPENAI_API_KEY"),
    },
    "huggingface": {
        "model_name": "mistralai/Mistral-7B-Instruct-v0.1",
        "temperature": 0.7,
        "max_tokens": 1000,
        "api_key": os.getenv("HUGGINGFACE_API_KEY"),
    }
}

# Logging Configuration
LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO"
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "penny.log",
            "formatter": "default",
            "level": "DEBUG"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"]
    }
}
