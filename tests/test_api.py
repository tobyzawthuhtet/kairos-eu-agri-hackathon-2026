import pytest
from fastapi.testclient import TestClient

from kairos.api.main import app
from kairos.serving import replay

pytestmark = pytest.mark.skipif(not replay.features(), reason="needs data/processed/features (run build_features.py)")
client = TestClient(app)


def test_meta_and_provinces():
    m = client.get("/meta").json()
    assert m["mode"] == "replay" and m["date_min"] == "2025-01-01"
    assert len(client.get("/provinces").json()) >= 8


def test_replay_day_shape():
    r = client.get("/replay/23", params={"date": "2025-07-20"})
    assert r.status_code == 200
    j = r.json()
    assert len(j["trail"]) == 14 and "alerts" in j and j["province"]["name"] == "Jaén"


def test_alerts_filters_and_advisory():
    a = client.get("/alerts", params={"province": "23", "severity": "moderate"}).json()
    assert a and all(x["province"] == "23" for x in a)
    adv = client.get(f"/advisories/{a[0]['rule_id']}").json()
    assert adv["review_status"] == "pending agronomist review" and adv["validated"] is False


def test_bad_inputs():
    assert client.get("/replay/23", params={"date": "nope"}).status_code == 422
    assert client.get("/replay/99", params={"date": "2025-07-20"}).status_code == 404
    assert client.get("/advisories/NOPE").status_code == 404
