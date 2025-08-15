from core.stt.factory import STTFactory
from core.tts.factory import TTSFactory
from core.vad.webrtc_vad import SimpleVAD
from core.telemetry import Telemetry
from core.llm_router import get_llm, load_config
from core.personality import apply

def run_once() -> dict:
    cfg = load_config()
    llm = get_llm()
    stt = STTFactory.create(cfg)
    vad = SimpleVAD()
    tts = TTSFactory.create(cfg)
    telemetry = Telemetry()
    prompt = "Hello"
    reply = llm.generate(prompt)
    out = apply(reply, cfg.get("personality", {}))
    audio = tts.speak(out)
    return {"text": out, "audio_len": len(audio)}

if __name__ == "__main__":
    print(run_once())
