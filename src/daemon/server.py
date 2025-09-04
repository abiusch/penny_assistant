import os
import time
import logging
import threading
from contextlib import asynccontextmanager
from typing import Optional
from time import perf_counter

from fastapi import FastAPI, Body, Request
from pydantic import BaseModel

from daemon.health import start_health_loop, stop_health_loop, set_health_callback
from daemon.metrics import METRICS


# ---- simple in-memory state for PTT ----
_PTT_ACTIVE = False
_PTT_LOCK = threading.Lock()


def _health_metrics_callback(success: bool, error_msg: str) -> None:
    """Update health metrics from health loop."""
    with METRICS.lock:
        METRICS._health_tick_count += 1
        if not success:
            METRICS._last_health_err = error_msg
        # Clear error on success (could also keep last error for debugging)
        elif not METRICS._last_health_err:
            METRICS._last_health_err = ""


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    set_health_callback(_health_metrics_callback)
    iv = os.getenv("PENNY_HEALTH_INTERVAL")
    start_health_loop(float(iv) if iv else None)
    logger.info("Daemon started")
    
    yield
    
    # Shutdown
    stop_health_loop()
    set_health_callback(None)
    logger.info("Daemon stopped")


logger = logging.getLogger("penny.daemon")
app = FastAPI(title="PennyGPT Daemon", lifespan=lifespan)


@app.middleware("http")
async def _metrics_middleware(request: Request, call_next):
    """Track request metrics and latencies."""
    t0 = perf_counter()
    try:
        response = await call_next(request)
        return response
    finally:
        latency_ms = (perf_counter() - t0) * 1000
        with METRICS.lock:
            METRICS._requests += 1
        METRICS.record_latency_ms(latency_ms)


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
        with METRICS.lock:
            METRICS._speak_fail += 1
        return False

    try:
        tts = GoogleTTS(config={})
        result = bool(tts.speak(text, voice_id=voice_id, ssml=ssml, allow_barge_in=True))
        with METRICS.lock:
            if result:
                METRICS._speak_ok += 1
            else:
                METRICS._speak_fail += 1
        return result
    except Exception as e:
        logger.warning("TTS speak failed: %s", e)
        with METRICS.lock:
            METRICS._speak_fail += 1
        return False


@app.get("/health")
def health():
    # Keep it cheap; don't do heavyweight checks here.
    return {
        "ok": True,
        "uptime_s": METRICS.snapshot()["uptime_s"],
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


@app.get("/metrics")
@app.get("/api/metrics")
def metrics():
    """Return comprehensive metrics for observability."""
    return METRICS.snapshot()


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
