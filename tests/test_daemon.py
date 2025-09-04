import os
os.environ["PENNY_DISABLE_HEALTH_LOOP"] = "1"  # keep tests quiet

from fastapi.testclient import TestClient  # type: ignore
from daemon.server import app

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert "uptime_s" in data


def test_ptt_cycle():
    a = client.post("/ptt/start").json()
    b = client.post("/ptt/stop").json()
    assert a["ok"] and b["ok"]
    assert a["ptt_active"] is True
    assert b["ptt_active"] is False


def test_speak_contract():
    # We only assert the response shape; adapter may be missing in CI.
    r = client.post("/speak", json={"text": "hi from test"})
    assert r.status_code == 200
    data = r.json()
    assert "ok" in data


def test_metrics_endpoints():
    # Test both /metrics and /api/metrics
    r1 = client.get("/metrics")
    r2 = client.get("/api/metrics")
    
    assert r1.status_code == 200
    assert r2.status_code == 200
    
    data1 = r1.json()
    data2 = r2.json()
    
    # Check required metrics fields for both endpoints
    expected_fields = [
        "schema_version", "requests", "speak_ok", "speak_fail", "tts_cache_hits",
        "health_tick_count", "last_health_err", "last_latency_ms",
        "p50_ms", "p95_ms", "speak_success_rate", "total_speak_requests", "uptime_s"
    ]
    
    for field in expected_fields:
        assert field in data1, f"Missing field in /metrics: {field}"
        assert field in data2, f"Missing field in /api/metrics: {field}"
    
    # Verify data types and schema version
    assert data1["schema_version"] == 1, "Schema version should be 1"
    assert data2["schema_version"] == 1, "Schema version should be 1"
    assert isinstance(data1["requests"], int)
    assert isinstance(data1["speak_success_rate"], float)
    assert isinstance(data1["uptime_s"], (int, float))
    assert isinstance(data1["last_health_err"], str)
    
    # Verify metrics are being tracked (requests should be > 0 from this test)
    assert data2["requests"] > 0
