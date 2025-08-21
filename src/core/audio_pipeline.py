from src.core.stt.factory import STTFactory
from src.core.tts.factory import TTSFactory
from src.core.vad.webrtc_vad import create_vad_engine
from src.core.telemetry import telemetry
from src.core.llm_router import get_llm, load_config
from src.core.personality import apply

def run_once() -> dict:
    cfg = load_config()
    llm = get_llm()
    stt = STTFactory.create(cfg)
    vad = create_vad_engine(cfg)
    tts = TTSFactory.create(cfg)
    prompt = "Hello"
    reply = llm.generate(prompt)
    out = apply(reply, cfg.get("personality", {}))
    try:
        tts.speak(out)
        audio_len = len(out.encode())  # Rough estimate based on text length
    except Exception:
        audio_len = 0
    return {"text": out, "audio_len": audio_len}

if __name__ == "__main__":
    print(run_once())
