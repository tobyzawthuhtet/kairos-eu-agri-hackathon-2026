import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agronomist"))
from kairos.rules import reviews
from kairos.rules.table_engine import load_ruleset


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(reviews, "FILE", tmp_path / "reviews.json")
    import app as agro

    agro.app.config["TESTING"] = True
    return agro.app.test_client()


def rule(rid):
    return next((r for r in load_ruleset().rules if r.rule_id == rid), None)


def test_pages_render(client):
    assert client.get("/").status_code == 200
    r = client.get("/scenario/OLV-S05-HEAT-02")
    assert r.status_code == 200 and b"Kairos warns the grower" in r.data
    assert client.get("/scenario/NOPE").status_code == 404
    assert client.get("/export.csv").data.startswith(b"crop,")


def test_approve_validates_rule_in_engine(client):
    assert rule("OLV-S05-HEAT-02").validated is False
    client.post("/scenario/OLV-S05-HEAT-02", data={"decision": "approved", "reviewer": "Dr Ruiz", "threshold": "35", "action": ""})
    assert rule("OLV-S05-HEAT-02").validated is True


def test_modify_changes_threshold_and_reject_removes_rule(client):
    client.post("/scenario/OLV-S05-HEAT-02", data={"decision": "modified", "reviewer": "Dr Ruiz", "threshold": "37", "action": "Irrigate at dawn."})
    r = rule("OLV-S05-HEAT-02")
    assert r.threshold == 37.0 and r.action == "Irrigate at dawn." and r.validated
    client.post("/scenario/OLV-S05-HEAT-02", data={"decision": "rejected", "reviewer": "Dr Ruiz", "threshold": "", "action": ""})
    assert rule("OLV-S05-HEAT-02") is None
    assert any(x["rule_id"] == "OLV-S05-HEAT-02" and "rejected" in x["reason"] for x in load_ruleset().not_evaluable)
    assert b"Rejected" in client.get("/").data and b"rejected" in client.get("/export.csv").data


def test_figure_data_endpoints(client):
    from kairos.serving import replay

    if not replay.features():
        pytest.skip("needs data/processed/features")
    ov = client.get("/api/overview").json
    assert ov["rules"] and len(ov["months"]) == len(ov["rules"]) and ov["stage_order"][0] == "dormancy_chilling"
    sr = client.get("/api/scenario/OLV-S05-HEAT-02/series").json
    assert sr["operator"] == ">=" and len(sr["provinces"]) > 15 and len(sr["dates"]) == len(sr["stage_active"]) == len(sr["provinces"][0]["v"])
    assert client.get("/api/scenario/OLV-S09-ANTH-02/series").status_code == 404  # not testable from weather
    page = client.get("/scenario/OLV-S05-HEAT-02").data
    assert b"fig-season" in page and b"Test the threshold" in page
