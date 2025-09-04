# src/daemon/metrics.py
from collections import deque
from threading import Lock
import time

class Metrics:
    def __init__(self):
        self._lock = Lock()
        self._requests = 0
        self._speak_ok = 0
        self._speak_fail = 0
        self._tts_cache_hits = 0  # you can wire this later
        self._health_tick_count = 0
        self._last_health_err = ""
        self._lat_ms = deque(maxlen=1000)
        self._start_ts = time.time()

    @property
    def lock(self):
        """Backward compatibility property for existing code."""
        return self._lock

    def record_latency_ms(self, ms: float) -> None:
        with self._lock:
            self._lat_ms.append(float(ms))

    def snapshot(self) -> dict:
        with self._lock:
            arr = sorted(self._lat_ms)
            def q(arr_, q_):
                if not arr_:
                    return 0
                idx = int(q_ * (len(arr_) - 1))
                return int(arr_[idx])
            
            total_speak = self._speak_ok + self._speak_fail
            rate = (self._speak_ok / total_speak) if total_speak else 0.0
            last_ms = int(arr[-1]) if arr else 0
            p50 = q(arr, 0.50)
            p95 = q(arr, 0.95)
            
            return {
                "schema_version": 1,
                "requests": self._requests,
                "last_latency_ms": last_ms,
                "p50_ms": p50,
                "p95_ms": p95,
                "speak_ok": self._speak_ok,
                "speak_fail": self._speak_fail,
                "speak_success_rate": round(rate, 3),
                "total_speak_requests": total_speak,
                "tts_cache_hits": self._tts_cache_hits,
                "health_tick_count": self._health_tick_count,
                "last_health_err": self._last_health_err,
                "uptime_s": round(time.time() - self._start_ts, 2),
            }

METRICS = Metrics()
