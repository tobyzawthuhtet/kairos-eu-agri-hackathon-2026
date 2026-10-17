"""Build demo/kairos-demo.html: one self-contained file (CSS + JS + 2025 replay snapshot, no network)."""
import json
from pathlib import Path

import pandas as pd

from kairos.serving import replay

ROOT = Path(__file__).resolve().parents[1]
COLS = ["tmin_c", "tmax_c", "tmean_c", "rh_mean_pct", "precip_mm", "precip_max_12h_mm", "wet_hours_8_24c",
        "soil_moisture_l1", "pev_mm", "gust_max_ms", "gdd_base9_1"]


def snapshot() -> dict:
    feats = replay.features()
    dates = [d.strftime("%Y-%m-%d") for d in next(iter(feats.values())).index]
    prov = {p["code"]: p for p in replay.provinces()}
    feat = {c: {k: [None if pd.isna(v) else round(float(v), 1) for v in df[k]] for k in COLS} for c, df in feats.items()}
    a = replay.alerts_table()
    alerts: dict[str, dict[str, list]] = {}
    rule_ids = set()
    for r in a.itertuples():
        alerts.setdefault(r.province, {}).setdefault(r.date.strftime("%Y-%m-%d"), []).append(
            [r.rule_id, r.hazard, r.severity, r.stage, r.value, r.operator, r.threshold, r.unit])
        rule_ids.add(r.rule_id)
    rules = {rid: replay.advisory(rid) for rid in sorted(rule_ids)}
    obs = {}
    ot = replay.observations_table()
    for r in ot.itertuples():
        obs.setdefault(r.province, []).append({
            "d": r.date.strftime("%Y-%m-%d"), "m": r.metric, "v": r.value if isinstance(r.value, str) else None,
            "n": None if pd.isna(r.num) else float(r.num), "u": None if pd.isna(r.unit) else r.unit,
            "s": None if pd.isna(r.stage_name) else r.stage_name, "z": None if pd.isna(r.zone) else r.zone,
            "p": r.date_precision})
    ne = {}
    for x in replay.not_evaluable():
        ne[x["reason"]] = ne.get(x["reason"], 0) + 1
    bt = replay.backtest()
    return {"meta": replay.meta(), "dates": dates, "provinces": list(prov.values()), "feat": feat, "alerts": alerts,
            "rules": rules, "obs": obs, "not_evaluable": ne, "backtest": bt}


def main() -> None:
    data = json.dumps(snapshot(), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = (ROOT / "demo/template.html").read_text().replace("/*__DATA__*/null", data)
    out = ROOT / "demo/kairos-demo.html"
    out.write_text(html)
    print(f"wrote {out} ({out.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
