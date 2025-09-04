# src/daemon/metrics.py
from collections import deque
from threading import Lock
import time

class Metrics:
    def __init__(self):
        self.lock = Lock()
        self.requests = 0
        self.speak_ok = 0
        self.speak_fail = 0
        self.tts_cache_hits = 0  # you can wire this later
        self.health_tick_count = 0
        self.last_health_err = ""
        self._lat_ms = deque(maxlen=1000)
        self.started_at = time.time()

    def record_latency_ms(self, ms: float) -> None:
        with self.lock:
            self._lat_ms.append(float(ms))

    def snapshot(self) -> dict:
        with self.lock:
            arr = sorted(self._lat_ms)
            def q(arr_, q_):
                if not arr_:
                    return 0
                idx = int(q_ * (len(arr_) - 1))
                return int(arr_[idx])
            total_speak = self.speak_ok + self.speak_fail
            success_rate = (self.speak_ok / total_speak) if total_speak else 0.0
            return {
                "requests": self.requests,
                "speak_ok": self.speak_ok,
                "speak_fail": self.speak_fail,
                "tts_cache_hits": self.tts_cache_hits,
                "health_tick_count": self.health_tick_count,
                "last_health_err": self.last_health_err,
                "last_latency_ms": int(arr[-1]) if arr else 0,
                "speak_success_rate": round(success_rate, 3),
                "total_speak_requests": total_speak,
                "p50_ms": q(arr, 0.50),
                "p95_ms": q(arr, 0.95),
                "uptime_s": round(time.time() - self.started_at, 2),
            }

METRICS = Metrics()
