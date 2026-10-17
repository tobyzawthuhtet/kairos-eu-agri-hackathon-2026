"""Data for the agronomist's interactive figures. Crop-level: province series weighted by the crop's area, never per farm plot."""
from functools import lru_cache
from pathlib import Path

import pandas as pd
import yaml

from kairos.config import CONFIG_DIR
from kairos.rules import reviews
from kairos.rules.table_engine import active_stages, evaluate, load_ruleset, stage_calendar
from kairos.serving import replay

FEATURE_LABEL = {
    "tmin_c": ("Daily minimum temperature", "°C"), "tmax_c": ("Daily maximum temperature", "°C"), "tmean_c": ("Daily mean temperature", "°C"),
    "precip_mm": ("Daily rain", "mm"), "precip_max_12h_mm": ("Wettest 12 hours of the day", "mm"), "wet_hours_8_24c": ("Leaf-wet hours at 8–24 °C (proxy)", "h"),
    "gust_max_ms": ("Strongest wind gust", "km/h"), "soil_temp_l1_c": ("Soil temperature, 0–7 cm", "°C"), "rh_min_pct": ("Lowest relative humidity", "%"),
    "rh_mean_pct": ("Mean relative humidity", "%"), "soil_moisture_l3": ("Soil moisture, 28–100 cm", "m³/m³"),
}
RAIF_FOR = {"peacock_spot": ("repilo_leaf_pct", "Peacock spot, % of leaves (RAIF)"), "peacock_spot_infection": ("repilo_leaf_pct", "Peacock spot, % of leaves (RAIF)"),
            "olive_fly": ("fly_punctured_pct", "Fly-punctured fruit, % (RAIF)"), "olive_fly_heat_suppression": ("fly_punctured_pct", "Fly-punctured fruit, % (RAIF)")}


def crops() -> list[str]:
    return sorted(p.name for p in (CONFIG_DIR / "crops").iterdir() if (p / "decision_table.csv").exists())


def has_weather(crop: str) -> bool:
    return crop == "olive" and bool(replay.features())  # province series are olive-area weighted


def _rule(crop: str, sid: str):
    return next((r for r in load_ruleset(crop).rules if r.rule_id == sid), None)


def _cmp(x: pd.Series, op: str, thr):
    if op == "between":
        return (x >= thr[0]) & (x <= thr[1])
    return {"<": x < thr, "<=": x <= thr, ">": x > thr, ">=": x >= thr}[op]


def series(crop: str, sid: str) -> dict | None:
    rule = _rule(crop, sid)
    if rule is None or not has_weather(crop):
        return None
    meta = replay.province_meta()
    feats = {c: f for c, f in replay.features().items() if not rule.regions or meta[c]["region"] in rule.regions}
    first = next(iter(feats.values()))
    dates = list(first.index)
    stage = [1 if set(rule.stages) & set(active_stages(d.date(), crop)) else 0 for d in dates]
    label, unit = FEATURE_LABEL.get(rule.feature, (rule.feature, ""))
    provs = []
    for code, df in feats.items():
        v = (df[rule.feature] * rule.scale).round(2)
        masks = [_cmp(df[w["feature"]], w["op"], tuple(w["value"]) if w["op"] == "between" else w["value"]).astype(int).tolist() for w in rule.when]
        provs.append({"code": code, "name": meta[code]["name"], "region": meta[code]["region"], "v": [None if pd.isna(x) else float(x) for x in v], "w": masks})
    raif = []
    key = RAIF_FOR.get(rule.hazard)
    if key and "andalucia" in {p["region"] for p in provs}:
        ot = replay.observations_table()
        if not ot.empty:
            o = ot[ot["metric"] == key[0]].dropna(subset=["num"])
            raif = [{"date": r.date.strftime("%Y-%m-%d"), "province": meta[r.province]["name"], "value": float(r.num)} for r in o.itertuples() if r.province in meta]
    return {"id": sid, "hazard": rule.hazard, "feature": rule.feature, "feature_label": label, "unit": unit,
            "operator": rule.operator, "threshold": list(rule.threshold) if rule.operator == "between" else rule.threshold, "stages": rule.stages,
            "when": [{"label": FEATURE_LABEL.get(w["feature"], (w["feature"], ""))[0], "op": w["op"], "value": w["value"]} for w in rule.when],
            "dates": [d.strftime("%Y-%m-%d") for d in dates], "stage_active": stage, "provinces": provs, "raif": raif,
            "raif_label": key[1] if key else None, "validated": rule.validated, "regions": sorted(rule.regions)}


@lru_cache
def _overview(crop: str, _mtime: float) -> dict:
    rs = load_ruleset(crop)
    meta = replay.province_meta()
    months = [[0] * 12 for _ in rs.rules]
    idx = {r.rule_id: i for i, r in enumerate(rs.rules)}
    for code, df in replay.features().items():
        a = evaluate(df, meta[code]["region"], crop)
        if a.empty:
            continue
        for (rid, m), g in a.groupby(["rule_id", a["date"].dt.month]):
            months[idx[rid]][m - 1] += len(g)
    return {"rules": [{"id": r.rule_id, "hazard": r.hazard, "stage": r.stages[0], "severity": r.severity, "validated": r.validated} for r in rs.rules], "months": months}


def overview(crop: str) -> dict:
    cal = {k: list(v) for k, v in stage_calendar(crop).items()}
    base = {"stages": cal, "crop": crop, "has_weather": has_weather(crop)}
    return {**base, **(_overview(crop, reviews.mtime()) if has_weather(crop) else {"rules": [], "months": []})}


def stage_names(crop: str) -> dict:
    return yaml.safe_load((Path(CONFIG_DIR) / "crops" / crop / "stage_calendar.yaml").read_text())["stages"]
