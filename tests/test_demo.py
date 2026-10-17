import json

import pytest
from fastapi.testclient import TestClient

from kairos.api.main import app
from kairos.demo import core

pytestmark = pytest.mark.skipif(not (core.DEMO / "farms.json").exists() or not (core.DEMO / "cell_features.csv.gz").exists(),
                                reason="needs data/processed/demo (run scripts/build_demo_farms.py)")


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(core, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(core, "_state", None)
    return TestClient(app)


def test_feed_has_advice_and_evidence(client):
    feed = client.get("/demo/farmers/F01/alerts").json()
    assert feed and feed[0]["advice"]["steps"] and feed[0]["evidence"]
    assert {e["tag"] for a in feed for e in a["evidence"]} <= {"General", "Your field"}


def test_farmer_to_advisor_roundtrip(client):
    aid = client.get("/demo/farmers/F01/alerts").json()[1]["id"]
    req = client.post("/demo/requests", json={"farmer_id": "F01", "alert_id": aid, "message": "check", "photos": []}).json()
    assert req["status"] == "asked" and any(r["id"] == req["id"] for r in client.get("/demo/requests", params={"status": "asked"}).json())
    out = client.post(f"/demo/requests/{req['id']}/respond", json={"decision": "edited", "text": "8 h", "headline": "Irrigate 8 hours", "steps": ["a", "b"]}).json()
    assert out["status"] == "replied"
    alert = client.get("/demo/alerts/" + aid).json()
    assert alert["review"]["status"] == "edited" and alert["review"]["headline"] == "Irrigate 8 hours"
    assert client.get("/demo/chat/F01").json()[-1]["from"] == "advisor"


def test_verified_report_warns_neighbours_without_identity(client):
    rep = client.get("/demo/reports", params={"status": "new"}).json()[0]
    ver = client.post(f"/demo/reports/{rep['id']}/verify", json={"action": "verify"}).json()
    assert ver["status"] == "verified" and ver["warned_farmers"]
    neighbour = ver["warned_farmers"][0]
    feed = client.get(f"/demo/farmers/{neighbour}/alerts").json()
    community = [a for a in feed if a.get("community")]
    assert len(community) == 1
    reporter = core.farmer_index()[rep["farmer_id"]]
    blob = json.dumps(community)
    assert reporter["name"] not in blob and reporter["farm"] not in blob


def test_dashboard_and_weather(client):
    d = client.get("/demo/dashboard").json()
    assert d["counts"]["parcels"] == len(d["parcels"]) > 20
    pid = d["parcels"][0]["id"]
    assert client.get(f"/demo/parcels/{pid}/weather").json()["tmax_c"]
    r = client.post("/demo/review/" + d["parcels"][0]["alerts"][0]["id"] if d["parcels"][0]["alerts"] else "/demo/review/x", json={"status": "bogus"})
    assert r.status_code == 422


def test_clock_bounds(client):
    assert client.post("/demo/clock", json={"date": "2030-01-01"}).status_code == 422
    assert client.post("/demo/clock", json={"date": "2025-07-01"}).json()["clock"] == "2025-07-01"
