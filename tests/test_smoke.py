from src.core.llm_router import get_llm
from src.core.audio_pipeline import run_once

def test_llm_router():
    llm = get_llm()
    out = llm.generate("ping")
    assert isinstance(out, str)

def test_run_once():
    res = run_once()
    assert "text" in res and isinstance(res["text"], str)
