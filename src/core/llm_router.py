from typing import Any
from src.runtime_paths import config_path, load_runtime_config

from adapters.llm.local_ollama_adapter import LocalLLM
from adapters.llm.cloud_openai_adapter import CloudLLM
from adapters.llm.gptoss_adapter import GPTOSS

_LLM_INSTANCE: Any | None = None


def _config_path() -> str:
    return str(config_path())


def _load_config() -> dict:
    return load_runtime_config()


def load_config() -> dict:
    """Public helper to access penny_config.json contents."""
    return _load_config()


def get_llm_info() -> dict:
    """Get information about the current LLM configuration."""
    cfg = _load_config()
    llm_cfg = cfg.get("llm", {})
    provider = llm_cfg.get("provider", "ollama").lower()
    mode = llm_cfg.get("mode", "local_first").lower()
    
    # Determine what will be used
    if provider == "gptoss":
        gptoss_instance = GPTOSS(cfg)
        if gptoss_instance.is_available():
            will_use = "GPT-OSS"
        else:
            local_id = llm_cfg.get("local", "ollama:llama3")
            will_use = local_id
    elif provider == "ollama" or mode in ("local_first", "local", "local-only"):
        local_id = llm_cfg.get("local", "ollama:llama3")
        will_use = local_id
    elif mode in ("cloud_first", "cloud", "cloud-only"):
        cloud_id = llm_cfg.get("cloud", "gpt-4o")
        will_use = cloud_id
    else:
        local_id = llm_cfg.get("local", "ollama:llama3")
        will_use = local_id
    
    return {
        "provider": provider,
        "mode": mode,
        "will_use": will_use,
        "config": llm_cfg
    }


def get_llm() -> Any:
    global _LLM_INSTANCE
    if _LLM_INSTANCE is not None:
        return _LLM_INSTANCE

    cfg = _load_config()
    llm_cfg = cfg.get("llm", {})
    provider = llm_cfg.get("provider", "ollama").lower()
    mode = llm_cfg.get("mode", "local_first").lower()
    
    # Handle different providers with fallback logic
    if provider == "gptoss":
        print("[LLM] Attempting to use GPT-OSS...")
        gptoss_instance = GPTOSS(cfg)
        
        if gptoss_instance.is_available():
            print("[LLM] ✅ GPT-OSS available")
            _LLM_INSTANCE = gptoss_instance
        else:
            print("[LLM] ❌ GPT-OSS not available, falling back to Ollama")
            local_id = llm_cfg.get("local", "ollama:llama3")
            _LLM_INSTANCE = LocalLLM(local_id)
            
    elif provider == "ollama" or mode in ("local_first", "local", "local-only"):
        local_id = llm_cfg.get("local", "ollama:llama3") 
        _LLM_INSTANCE = LocalLLM(local_id)
        print(f"[LLM] Using Ollama: {local_id}")
        
    elif mode in ("cloud_first", "cloud", "cloud-only"):
        cloud_id = llm_cfg.get("cloud", "gpt-4o")
        _LLM_INSTANCE = CloudLLM(cloud_id)
        print(f"[LLM] Using Cloud: {cloud_id}")
        
    else:
        # Default fallback
        local_id = llm_cfg.get("local", "ollama:llama3")
        _LLM_INSTANCE = LocalLLM(local_id)
        print(f"[LLM] Default fallback to Ollama: {local_id}")

    return _LLM_INSTANCE


def reset_llm() -> None:
    global _LLM_INSTANCE
    _LLM_INSTANCE = None
