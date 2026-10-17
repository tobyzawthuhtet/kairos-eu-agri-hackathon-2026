"""Replay service: serves precomputed 2025 province features, rule alerts and RAIF observations.

ERA5 is reanalysis, so there is no live forecast. Any past day can be treated as "today" for the demo.
"""
import json
import math
from functools import lru_cache
from pathlib import Path

import pandas as pd
import yaml

from kairos.config import CONFIG_DIR
from kairos.rules.table_engine import (
    SEVERITY_RANK,
    active_stages,
    evaluate,
    load_ruleset,
    top_per_hazard,
)

ROOT = Path(__file__).resolve().parents[3]
FEATURES = ROOT / "data/processed/features"
BACKTEST = ROOT / "data/processed/backtest"
GDD_FULL_FLOWERING = 495.0  # decision table OLV-S03-PHEN-02 (Picual); release assumed 1 Jan
FEATURE_COLS = ["tmin_c", "tmax_c", "tmean_c", "rh_mean_pct", "precip_mm", "precip_max_12h_mm",
                "wet_hours_8_24c", "soil_moisture_l1", "pev_mm", "gust_max_ms", "gdd_base9_1"]
MODE = "replay"


def _clean(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return v.item() if hasattr(v, "item") else v


def _records(df: pd.DataFrame) -> list[dict]:
    return [{k: _clean(v) for k, v in r.items()} for r in df.to_dict("records")]


@lru_cache
def province_meta() -> dict[str, dict]:
    meta = yaml.safe_load((CONFIG_DIR / "provinces.yaml").read_text())
    w = pd.read_csv(ROOT / "data/processed/olive_weights.csv", dtype={"province": str})
    ha = w.groupby("province")["olive_ha"].sum()
    return {code: {"code": code, **m, "olive_ha": round(float(ha.get(code, 0.0)))} for code, m in meta.items()}


@lru_cache
def features() -> dict[str, pd.DataFrame]:
    out = {}
    for code, m in province_meta().items():
        f = FEATURES / f"{m['region']}_{code}.csv"
        if f.exists():
            df = pd.read_csv(f, parse_dates=["date"]).set_index("date")
            df["gdd_cum"] = df["gdd_base9_1"].cumsum()
            out[code] = df
    return out


@lru_cache
def alerts_table() -> pd.DataFrame:
    frames = []
    for code, df in features().items():
        a = top_per_hazard(evaluate(df, province_meta()[code]["region"]))
        if not a.empty:
            frames.append(a.assign(province=code))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


@lru_cache
def observations_table() -> pd.DataFrame:
    f = BACKTEST / "labels_2025.csv"
    if not f.exists():
        return pd.DataFrame()
    d = pd.read_csv(f, parse_dates=["date"])
    code_by_name = {m["name"]: c for c, m in province_meta().items()}
    d["province"] = d["province"].map(code_by_name)
    return d.dropna(subset=["province"])


def date_range() -> tuple[str, str]:
    idx = next(iter(features().values())).index
    return str(idx.min().date()), str(idx.max().date())


def meta() -> dict:
    lo, hi = date_range()
    rs = load_ruleset()
    return {"crop": "olive", "mode": MODE, "date_min": lo, "date_max": hi,
            "notice": "Replay of ERA5-Land reanalysis; thresholds are not yet agronomist-validated.",
            "rules_evaluable": len(rs.rules), "rules_not_evaluable": len(rs.not_evaluable),
            "provinces_with_features": len(features())}


def provinces() -> list[dict]:
    return [m for c, m in province_meta().items() if c in features()]


def day(province: str, d: str, trail_days: int = 14) -> dict | None:
    if province not in features():
        return None
    df = features()[province]
    ts = pd.Timestamp(d)
    if ts not in df.index:
        return None
    trail = df.loc[ts - pd.Timedelta(days=trail_days - 1): ts, FEATURE_COLS].reset_index()
    trail["date"] = trail["date"].dt.strftime("%Y-%m-%d")
    cur = df.loc[ts]
    a = alerts_table()
    today = a[(a["province"] == province) & (a["date"] == ts)] if not a.empty else a
    gdd = float(cur["gdd_cum"])
    return {"province": province_meta()[province], "date": d, "stages": active_stages(ts.date()),
            "features": {k: _clean(float(cur[k])) for k in FEATURE_COLS},
            "bloom": {"gdd_since_jan1": round(gdd, 1), "gdd_full_flowering": GDD_FULL_FLOWERING,
                      "reached": gdd >= GDD_FULL_FLOWERING, "assumption": "dormancy release = 1 Jan"},
            "trail": _records(trail), "alerts": _alert_records(today)}


def _alert_records(df: pd.DataFrame) -> list[dict]:
    if df is None or df.empty:
        return []
    df = df.assign(_r=df["severity"].map(SEVERITY_RANK)).sort_values("_r", ascending=False).drop(columns="_r")
    df = df.assign(date=df["date"].dt.strftime("%Y-%m-%d"))
    return _records(df)


def alerts(d: str | None = None, province: str | None = None, severity: str | None = None) -> list[dict]:
    a = alerts_table()
    if a.empty:
        return []
    if d:
        a = a[a["date"] == pd.Timestamp(d)]
    if province:
        a = a[a["province"] == province]
    if severity:
        a = a[a["severity"] == severity]
    return _alert_records(a)


def advisory(rule_id: str) -> dict | None:
    rs = load_ruleset()
    r = next((x for x in rs.rules if x.rule_id == rule_id), None)
    if not r:
        return None
    return {"rule_id": r.rule_id, "hazard": r.hazard, "severity": r.severity, "stages": r.stages,
            "feature": r.feature, "operator": r.operator,
            "threshold": r.threshold if r.operator != "between" else list(r.threshold), "unit": r.unit,
            "action": r.action, "lead_time_h": r.lead_time_h, "confidence": r.confidence,
            "validated": r.validated, "source_url": r.source_url, "window_notes": r.window_notes,
            "proxy_note": r.note, "review_status": "pending agronomist review"}


def not_evaluable() -> list[dict]:
    return load_ruleset().not_evaluable


def observations(province: str, d: str, window_days: int = 21) -> list[dict]:
    o = observations_table()
    if o.empty:
        return []
    ts = pd.Timestamp(d)
    o = o[(o["province"] == province) & ((o["date"] - ts).abs() <= pd.Timedelta(days=window_days))]
    o = o.assign(date_iso=o["date"].dt.strftime("%Y-%m-%d"))
    cols = ["date_iso", "date_precision", "metric", "value", "unit", "stage_code", "stage_name", "zone", "level"]
    return _records(o[[c for c in cols if c in o]].sort_values("date_iso"))


def backtest() -> dict:
    f = BACKTEST / "results.json"
    return json.loads(f.read_text()) if f.exists() else {}
