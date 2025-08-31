"""LLM Factory for creating language model instances."""

from adapters.llm.local_ollama_adapter import LocalLLM
from adapters.llm.cloud_openai_adapter import CloudLLM
from adapters.llm.gptoss_adapter import GPTOSS
from adapters.llm.openai_compat import OpenAICompatLLM

def create_llm_engine(config):
    """Create LLM engine based on configuration."""
    llm_config = config.get('llm', {})
    llm_type = llm_config.get('type', 'local')
    llm_mode = llm_config.get('mode', 'local_first')
    llm_provider = llm_config.get('provider', '')
    
    # Get model IDs
    local_model = llm_config.get('model', 'llama2')
    cloud_model = llm_config.get('cloud_model', 'gpt-4')
    
    # Check for specific provider first
    if llm_provider.lower() in ("openai_compatible", "openai-compatible", "lmstudio"):
        return OpenAICompatLLM(config)
    elif llm_provider == 'gptoss' or llm_type == 'gptoss':
        return GPTOSS(config)
    elif llm_type == 'local' or llm_mode in ('local_first', 'local', 'local-only'):
        return LocalLLM(local_model)
    elif llm_type == 'cloud' or llm_mode in ('cloud_first', 'cloud', 'cloud-only'):
        return CloudLLM(cloud_model)
    else:
        # Default to local
        return LocalLLM(local_model)

class LLMFactory:
    """Factory for LLM engines."""
    
    @staticmethod
    def create(config):
        return create_llm_engine(config)
    
    @staticmethod
    def from_config(config):
        return create_llm_engine(config)
