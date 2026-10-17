"""Decision-table rule engine: evaluates configs/crops/<crop>/decision_table.csv on daily features.

Crop-agnostic: a new crop only needs its own decision_table.csv, feature_map.yaml and stage_calendar.yaml.
Rows that cannot be evaluated from daily weather features are returned with a reason, never dropped.
"""
import re
from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache

import pandas as pd
import yaml

from kairos.config import CONFIG_DIR

SEVERITY = {"l": "low", "low": "low", "m": "moderate", "medium": "moderate", "h": "high", "high": "high",
            "critical": "severe", "info": "info"}
SEVERITY_RANK = {"info": 0, "low": 1, "moderate": 2, "high": 3, "severe": 4}


@dataclass
class Rule:
    rule_id: str
    stages: list[str]
    hazard: str
    severity: str
    feature: str
    scale: float
    operator: str
    threshold: tuple[float, float] | float
    unit: str
    when: list[dict]
    action: str
    lead_time_h: float | None
    regions: set[str]
    source_url: str
    confidence: str
    validated: bool
    note: str
    window_notes: str


@dataclass
class RuleSet:
    rules: list[Rule] = field(default_factory=list)
    not_evaluable: list[dict] = field(default_factory=list)


REGION_TOKENS = {"andalucia": "andalucia", "es-an": "andalucia", "castilla": "castilla_la_mancha", "es-cm": "castilla_la_mancha",
                 "extremadura": "extremadura", "es-ex": "extremadura", "cataluna": "cataluna", "es-ct": "cataluna",
                 "comunitat": "comunitat_valenciana", "es-vc": "comunitat_valenciana"}


def parse_regions(raw: str) -> set[str]:
    """Free-text `regions` cell ('Andalucia;Castilla-La Mancha', 'ES-AN|ES-CM', ...) -> region ids."""
    low = raw.lower()
    return {rid for tok, rid in REGION_TOKENS.items() if tok in low}


def _crop_dir(crop: str):
    return CONFIG_DIR / "crops" / crop


def _threshold(raw: str, op: str):
    s = str(raw).strip()
    if op == "between":
        lo, hi = re.split(r"\s*-\s*", s, maxsplit=1)
        return float(lo), float(hi)
    return float(s)


@lru_cache
def load_ruleset(crop: str = "olive") -> RuleSet:
    table = pd.read_csv(_crop_dir(crop) / "decision_table.csv", dtype=str).fillna("")
    fmap = yaml.safe_load((_crop_dir(crop) / "feature_map.yaml").read_text())
    out = RuleSet()
    for _, r in table.iterrows():
        rid = r["scenario_id"]

        def skip(reason: str, rid=rid, r=r) -> None:
            out.not_evaluable.append({"rule_id": rid, "stage": r["stage"], "hazard": r["hazard"],
                                      "data_class": r["data_class"], "variable": r["variable"], "reason": reason})

        if r["data_class"] != "climate":
            skip({"field_observation": "needs field scouting or a sample count",
                  "external_event": "needs an external event feed (hail / warnings)",
                  "calendar": "calendar reminder, not weather-driven"}.get(r["data_class"], "not a weather rule"))
            continue
        if r["threshold_status"] != "set":
            skip("no sourced threshold yet")
            continue
        if r["aggregation"] == "season":
            skip("seasonal aggregate, not a daily trigger")
            continue
        sk = next((s for s in fmap["skip"] if re.search(s["match"], r["variable"])), None)
        if sk:
            skip(sk["reason"])
            continue
        m = next((x for x in fmap["map"] if re.search(x["match"], r["variable"])), None)
        if not m:
            skip("no feature mapping for this variable")
            continue
        op = r["operator"]
        try:
            thr = _threshold(r["threshold"], op)
        except ValueError:
            skip(f"threshold '{r['threshold']}' not numeric")
            continue
        sev = SEVERITY.get(r["severity"].strip().lower(), "info")
        lead = float(r["action_lead_time_h"]) if r["action_lead_time_h"].replace(".", "", 1).isdigit() else None
        out.rules.append(Rule(
            rule_id=rid, stages=r["stage"].split("|"), hazard=r["hazard"], severity=sev, feature=m["feature"],
            scale=float(m.get("scale", 1.0)), operator=op, threshold=thr, unit=r["unit"], when=m.get("when", []),
            action=r["action"], lead_time_h=lead,
            regions=parse_regions(r["regions"]), source_url=r["source_url"],
            confidence=r["confidence"], validated=r["validated"].strip().lower() == "true",
            note=m.get("note", ""), window_notes=r["window_notes"]))
    return out


@lru_cache
def stage_calendar(crop: str = "olive") -> dict[str, tuple[str, str]]:
    cal = yaml.safe_load((_crop_dir(crop) / "stage_calendar.yaml").read_text())["stages"]
    return {k: (v[0], v[1]) for k, v in cal.items()}


def active_stages(day: date, crop: str = "olive") -> list[str]:
    key = day.strftime("%m-%d")
    on = []
    for name, (a, b) in stage_calendar(crop).items():
        if (a <= key <= b) if a <= b else (key >= a or key <= b):
            on.append(name)
    return on


def _cmp(x: pd.Series, op: str, thr) -> pd.Series:
    if op == "between":
        return (x >= thr[0]) & (x <= thr[1])
    return {"<": x < thr, "<=": x <= thr, ">": x > thr, ">=": x >= thr}[op]


def evaluate(features: pd.DataFrame, region: str, crop: str = "olive") -> pd.DataFrame:
    """Evaluate every weather rule on one province's daily features. Index must be datetime."""
    rs = load_ruleset(crop)
    stages_by_day = {d: set(active_stages(d.date(), crop)) for d in features.index}
    rows = []
    for rule in rs.rules:
        if rule.regions and region not in rule.regions:
            continue
        if rule.feature not in features:
            continue
        x = features[rule.feature] * rule.scale
        hit = _cmp(x, rule.operator, rule.threshold)
        for w in rule.when:
            hit &= _cmp(features[w["feature"]], w["op"], tuple(w["value"]) if w["op"] == "between" else w["value"])
        for day in features.index[hit.fillna(False)]:
            if not (set(rule.stages) & stages_by_day[day]):
                continue
            rows.append({"date": day, "rule_id": rule.rule_id, "hazard": rule.hazard, "severity": rule.severity,
                         "stage": "|".join(sorted(set(rule.stages) & stages_by_day[day])),
                         "value": round(float(x[day]), 2), "operator": rule.operator,
                         "threshold": rule.threshold if rule.operator != "between" else f"{rule.threshold[0]}-{rule.threshold[1]}",
                         "unit": rule.unit, "action": rule.action, "lead_time_h": rule.lead_time_h,
                         "confidence": rule.confidence, "validated": rule.validated,
                         "source_url": rule.source_url, "note": rule.note})
    return pd.DataFrame(rows)


def top_per_hazard(alerts: pd.DataFrame) -> pd.DataFrame:
    """Keep the most severe firing rule per (date, hazard) so nested warning levels don't stack."""
    if alerts.empty:
        return alerts
    a = alerts.assign(_r=alerts["severity"].map(SEVERITY_RANK))
    a = a.sort_values(["date", "hazard", "_r"], ascending=[True, True, False])
    return a.drop_duplicates(["date", "hazard"]).drop(columns="_r").reset_index(drop=True)
