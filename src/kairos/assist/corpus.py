"""Decision-table rows as retrievable documents."""
from functools import lru_cache

import pandas as pd

from kairos.config import CONFIG_DIR
from kairos.rules import reviews

TABLE = CONFIG_DIR / "crops/{crop}/decision_table.csv"


@lru_cache(maxsize=4)
def _load(crop: str, _mtime: float) -> list[dict]:
    df = pd.read_csv(str(TABLE).format(crop=crop)).fillna("")
    rv = reviews.load()
    docs = []
    for r in df.to_dict("records"):
        rid = r["scenario_id"]
        rev = rv.get(rid, {})
        thr = f"{r['variable']} {r['aggregation']} {r['operator']} {r['threshold']} {r['unit']}".strip() if r["threshold_status"] == "set" else "no numeric threshold (needs field observation)"
        text = (f"Rule {rid}. Crop stage: {r['stage']}. Hazard: {r['hazard']}. Trigger: {thr}; duration {r['duration']}. "
                f"Evidence: {r['window_notes']} Action: {r['action']} Lead time: {r['action_lead_time_h'] or 'not given'} h. "
                f"Confidence: {r['confidence']}. Validated by agronomist: {rev.get('status') == 'approved' or str(r['validated']).lower() == 'true'}."
                + (f" Agronomist note ({rev.get('status')}): {rev.get('comment')}" if rev.get("comment") else "")
                + (f" Agronomist-adjusted threshold: {rev['threshold']}." if rev.get("threshold") else "")
                + (f" Agronomist-adjusted action: {rev['action']}." if rev.get("action") else ""))
        docs.append({"id": rid, "stage": r["stage"], "hazard": r["hazard"], "text": text, "source_url": r["source_url"], "row": r})
    return docs


def documents(crop: str = "olive") -> list[dict]:
    return _load(crop, reviews.mtime())
