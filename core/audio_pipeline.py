from adapters.stt.whisper_adapter import STTWhisper
from adapters.tts.google_tts_adapter import GoogleTTS
from adapters.vad.webrtc_vad_adapter import WebRTCVAD
from core.llm_router import get_llm, load_config
from core.personality import apply

def run_once() -> dict:
    cfg = load_config()
    llm = get_llm()
    stt = STTWhisper({**cfg.get("stt", {}), "dry_run": True})
    vad = WebRTCVAD(cfg.get("vad", {}))
    tts = GoogleTTS({**cfg.get("tts", {}), "dry_run": True})
    prompt = "Hello"
    reply = llm.generate(prompt)
    out = apply(reply, cfg.get("personality", {}))
    audio = tts.speak(out)
    return {"text": out, "audio_len": len(audio)}

if __name__ == "__main__":
    print(run_once())
