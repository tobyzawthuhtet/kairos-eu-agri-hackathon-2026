"""Advisor feedback on assistant answers. Approved/corrected answers become few-shot examples; the log is the future fine-tuning set."""
import json
import threading
import uuid
from datetime import UTC, datetime

from kairos.rules.reviews import ROOT

FILE = ROOT / "data/processed/assist/feedback.jsonl"
_LOCK = threading.Lock()
VERDICTS = ("good", "corrected", "bad")


def log_answer(question: str, result: dict, alert_id: str | None, hazard: str | None) -> str:
    return _append({"kind": "answer", "question": question, "answer": result["text"], "backend": result["backend"], "alert_id": alert_id,
                    "hazard": hazard, "cites": [c["rule_id"] for c in result["citations"]]})


def _append(rec: dict) -> str:
    rec = {"id": rec.get("id") or uuid.uuid4().hex[:10], "at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M"), **rec}
    with _LOCK:
        FILE.parent.mkdir(parents=True, exist_ok=True)
        with FILE.open("a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec["id"]


def rate(answer_id: str, verdict: str, advisor: str, corrected: str = "", note: str = "") -> None:
    if verdict not in VERDICTS:
        raise ValueError(f"verdict must be one of {VERDICTS}")
    _append({"kind": "rating", "answer_id": answer_id, "verdict": verdict, "advisor": advisor, "corrected": corrected, "note": note})


def records() -> list[dict]:
    return [json.loads(line) for line in FILE.read_text().splitlines() if line.strip()] if FILE.exists() else []


def examples(hazard: str | None, n: int = 2) -> list[dict]:
    """Latest advisor-approved (or corrected) Q/A pairs for a hazard, newest first."""
    recs = records()
    answers = {r["id"]: r for r in recs if r["kind"] == "answer"}
    out = []
    for r in reversed(recs):
        a = answers.get(r.get("answer_id", ""))
        if r["kind"] != "rating" or not a or r["verdict"] == "bad" or (hazard and a["hazard"] != hazard):
            continue
        out.append({"question": a["question"], "answer": r["corrected"] or a["answer"]})
        if len(out) == n:
            break
    return out


def export_sft(path: str) -> int:
    """Chat-format JSONL of advisor-approved/corrected answers, ready for LoRA fine-tuning once there are enough."""
    recs = records()
    answers = {r["id"]: r for r in recs if r["kind"] == "answer"}
    rows = [{"messages": [{"role": "user", "content": answers[r["answer_id"]]["question"]},
                          {"role": "assistant", "content": r["corrected"] or answers[r["answer_id"]]["answer"]}]}
            for r in recs if r["kind"] == "rating" and r["verdict"] != "bad" and r["answer_id"] in answers]
    with open(path, "w") as f:
        f.writelines(json.dumps(x, ensure_ascii=False) + "\n" for x in rows)
    return len(rows)
