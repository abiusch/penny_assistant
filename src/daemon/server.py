import os
import time
import logging
import threading
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Body
from pydantic import BaseModel

from daemon.health import start_health_loop, stop_health_loop

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    iv = os.getenv("PENNY_HEALTH_INTERVAL")
    start_health_loop(float(iv) if iv else None)
    logger.info("Daemon started")
    
    yield
    
    # Shutdown
    stop_health_loop()
    logger.info("Daemon stopped")


logger = logging.getLogger("penny.daemon")
app = FastAPI(title="PennyGPT Daemon", lifespan=lifespan)

# ---- simple in-memory state for PTT ----
_PTT_ACTIVE = False
_PTT_LOCK = threading.Lock()
_START_TS = time.time()


class SpeakRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None
    ssml: Optional[str] = None


def _say(text: str, voice_id: Optional[str] = None, ssml: Optional[str] = None) -> bool:
    """Speak via Google TTS adapter; fail safely."""
    try:
        # Signature you gave me:
        # GoogleTTS(config).speak(text: str, voice_id=None, ssml=None, allow_barge_in=True) -> bool
        from adapters.tts.google_tts_adapter import GoogleTTS
    except Exception:
        logger.warning("GoogleTTS adapter not available")
        return False

    try:
        tts = GoogleTTS(config={})
        return bool(tts.speak(text, voice_id=voice_id, ssml=ssml, allow_barge_in=True))
    except Exception as e:
        logger.warning("TTS speak failed: %s", e)
        return False


@app.get("/health")
def health():
    # Keep it cheap; don’t do heavyweight checks here.
    return {
        "ok": True,
        "uptime_s": round(time.time() - _START_TS, 2),
        "ptt_active": _PTT_ACTIVE,
        "interval_s": float(os.getenv("PENNY_HEALTH_INTERVAL", "30")),
        "pid": os.getpid(),
    }


@app.post("/ptt/start")
def ptt_start():
    global _PTT_ACTIVE
    with _PTT_LOCK:
        _PTT_ACTIVE = True
    return {"ok": True, "ptt_active": True}


@app.post("/ptt/stop")
def ptt_stop():
    global _PTT_ACTIVE
    with _PTT_LOCK:
        _PTT_ACTIVE = False
    return {"ok": True, "ptt_active": False}


@app.post("/speak")
def speak(req: SpeakRequest = Body(...)):
    ok = _say(req.text, voice_id=req.voice_id, ssml=req.ssml)
    return {"ok": bool(ok)}


if __name__ == "__main__":
    # Allow `PYTHONPATH=src python3 src/daemon/server.py` to work
    logging.basicConfig(
        level=os.getenv("PENNY_LOG_LEVEL", "INFO"),
        format="%(levelname)s %(name)s: %(message)s",
    )
    import uvicorn

    uvicorn.run(
        "daemon.server:app",
        host=os.getenv("PENNY_HOST", "127.0.0.1"),
        port=int(os.getenv("PENNY_PORT", "8080")),
        reload=bool(int(os.getenv("PENNY_RELOAD", "0"))),
    )
