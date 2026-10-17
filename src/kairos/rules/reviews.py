"""Agronomist reviews of decision-table scenarios, stored next to the data (not in the literature table).

Statuses: approved (validated as is), modified (validated with the agronomist's threshold/action), rejected (never fires),
unsure (needs a field check; stays unvalidated). The rule engine reads this file, so a review changes live alerts.
"""
import json
import threading
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FILE = ROOT / "data/processed/agronomist/reviews.json"
STATUSES = ("approved", "modified", "rejected", "unsure")
_LOCK = threading.Lock()


def mtime() -> float:
    return FILE.stat().st_mtime if FILE.exists() else 0.0


def load() -> dict[str, dict]:
    return json.loads(FILE.read_text()) if FILE.exists() else {}


def save_review(scenario_id: str, status: str, reviewer: str, comment: str = "", threshold: str | None = None,
                action: str | None = None, duration: str | None = None, original: dict | None = None) -> dict:
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    with _LOCK:
        data = load()
        prev = data.get(scenario_id, {})
        entry = {"status": status, "reviewer": reviewer or "agronomist", "comment": comment, "at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M"),
                 "threshold": threshold or None, "action": action or None, "duration": duration or None, "original": original or prev.get("original"),
                 "history": [*prev.get("history", []), {k: prev[k] for k in ("status", "reviewer", "comment", "at", "threshold", "action") if k in prev}] if prev else []}
        data[scenario_id] = entry
        FILE.parent.mkdir(parents=True, exist_ok=True)
        FILE.write_text(json.dumps(data, ensure_ascii=False, indent=1))
        return entry
