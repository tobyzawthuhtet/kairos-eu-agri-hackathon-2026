import pytest

from kairos.assist import ask, feedback, llm
from kairos.assist.retrieve import retrieve


@pytest.fixture(autouse=True)
def _isolated_feedback(tmp_path, monkeypatch):
    monkeypatch.setattr(feedback, "FILE", tmp_path / "feedback.jsonl")


def test_retrieve_filters_by_hazard():
    ids = [d["hazard"] for d in retrieve("what do I do after frost", k=3)]
    assert ids and all(h == "frost" for h in ids)


def test_verify_flags_invented_numbers():
    assert ask.verify("Spray at 35 C [OLV-S01-FROST-01]", "threshold 35 C") == []
    assert ask.verify("Spray at 40 C", "threshold 35 C") == ["40"]


def test_falls_back_without_model(monkeypatch):
    monkeypatch.setattr(llm, "available", lambda: False)
    out = ask.answer("why?", {"title": "t", "summary": "s", "severity_ui": "High", "rule": {"id": "OLV-S01-FROST-01"},
                              "evidence": [], "advice": {"headline": "Do X.", "steps": ["Y."]}})
    assert out["backend"] == "template" and "Do X." in out["text"]


def test_rejects_ungrounded_model_answer(monkeypatch):
    monkeypatch.setattr(llm, "available", lambda: True)
    monkeypatch.setattr(llm, "chat", lambda *a, **k: "Apply 999 kg of copper.")
    out = ask.answer("what to apply?")
    assert out["backend"] == "template" and out["unsupported_numbers"] == ["999"]


def test_feedback_roundtrip(tmp_path, monkeypatch):
    aid = feedback.log_answer("q?", {"text": "a", "backend": "ollama", "citations": []}, "x", "frost")
    feedback.rate(aid, "corrected", "Elena", corrected="better a")
    assert feedback.examples("frost") == [{"question": "q?", "answer": "better a"}]
    assert feedback.examples("heat") == []
    assert feedback.export_sft(str(tmp_path / "sft.jsonl")) == 1


def test_feedback_endpoints(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from kairos.api.main import app

    c = TestClient(app)
    aid = feedback.log_answer("q?", {"text": "a", "backend": "template", "citations": []}, None, "frost")
    assert c.post("/demo/assist/feedback", json={"answer_id": aid, "verdict": "good"}).status_code == 200
    kinds = [r["kind"] for r in c.get("/demo/assist/feedback").json()]
    assert kinds == ["answer", "rating"]


def test_explain_falls_back_to_facts(monkeypatch):
    monkeypatch.setattr(llm, "available", lambda: False)
    out = ask.explain({"id": "a|1", "title": "Frost", "summary": "Low fell", "hazard": "frost", "severity_ui": "High", "source": "Decision table",
                       "rule": {"id": "OLV-S01-FROST-01", "value": -8, "operator": "<=", "threshold": -7, "unit": "C", "validated": False},
                       "evidence": [], "advice": {"headline": "h", "steps": [], "confidence": "Low confidence"}})
    assert out["backend"] == "template" and "not yet validated" in out["text"] and out["id"]


def test_verify_ignores_list_numbering():
    assert ask.verify("1. Fired at 21 %\n2. Source [OLV-S01-FROST-01]\n3. Check", "reading 21 %") == []
