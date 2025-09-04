import os
import threading
import logging
from typing import Optional

logger = logging.getLogger("penny.daemon")

_HEALTH_THREAD: Optional[threading.Thread] = None
_HEALTH_STOP = threading.Event()


def _health_tick() -> None:
    """Put your real checks here (LLM, TTS, devices, etc.)."""
    try:
        # e.g. llm.health(); tts.health(); devices.health()
        pass
    except Exception as e:
        logger.warning("Health check failed: %s", e)


def _health_loop(stop_evt: threading.Event, interval: float) -> None:
    while not stop_evt.wait(interval):
        logger.debug("PennyGPT health tick")
        _health_tick()


def start_health_loop(interval: Optional[float] = None) -> None:
    """Start background health loop. No-op if disabled or already running."""
    global _HEALTH_THREAD

    if os.getenv("PENNY_DISABLE_HEALTH_LOOP") == "1":
        logger.info("Health loop disabled by env")
        return

    # Default to 30s; clamp to >=1s to avoid spam
    iv = float(interval or os.getenv("PENNY_HEALTH_INTERVAL", "30"))
    if iv < 1:
        logger.warning("PENNY_HEALTH_INTERVAL < 1s; clamping to 1s")
        iv = 1.0

    if _HEALTH_THREAD and _HEALTH_THREAD.is_alive():
        return

    _HEALTH_STOP.clear()
    _HEALTH_THREAD = threading.Thread(
        target=_health_loop, args=(_HEALTH_STOP, iv), daemon=True
    )
    _HEALTH_THREAD.start()
    logger.info("Health loop started (interval=%.1fs)", iv)


def stop_health_loop() -> None:
    """Stop background health loop if running."""
    if _HEALTH_THREAD and _HEALTH_THREAD.is_alive():
        _HEALTH_STOP.set()
        _HEALTH_THREAD.join(timeout=2)
        logger.info("Health loop stopped")


__all__ = ["start_health_loop", "stop_health_loop"]
