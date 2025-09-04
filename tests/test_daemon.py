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
