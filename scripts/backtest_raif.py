"""Back-test 2025 ERA5-derived olive features against RAIF Andalucía reports.

Three checks, none of which tunes a threshold:
  1. phenology  - GDD(base 9.1) full-flowering date vs the dates RAIF reports stage F
  2. repilo     - cumulative leaf-wetness hours vs % leaves with peacock spot (lag scan)
  3. fly        - hot days (Tmax >= 35 C) vs punctured fruit %

Outputs data/processed/backtest/{labels_2025.csv,results.json}. Run build_features.py first.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/processed/backtest"
PROV = {"Almería": "04", "Cádiz": "11", "Córdoba": "14", "Granada": "18",
        "Huelva": "21", "Jaén": "23", "Málaga": "29", "Sevilla": "41"}
GOOD_PAIRING = {"provincial", "list", "nearest", "nearest_date", "provincial+relative_dates",
                "nearest_date+relative_dates"}
FULL_FLOWERING_GDD = 495.0  # decision table OLV-S03-PHEN-01..04 (Picual 495; range 488-510)
PRECISION_DAYS = {"day": 0, "part_of_month": 5, "month": 15, "inherited": 15}  # +/- half-width of the label date


def load_features() -> dict[str, pd.DataFrame]:
    feats = {}
    for name, code in PROV.items():
        f = ROOT / f"data/processed/features/andalucia_{code}.csv"
        if f.exists():
            feats[name] = pd.read_csv(f, parse_dates=["date"]).set_index("date")
    return feats


def clean_labels() -> pd.DataFrame:
    d = pd.read_csv(ROOT / "data/processed/ground_truth/raif_olive_labels.csv", dtype={"value": str})
    d["date"] = pd.to_datetime(d["date_iso"], errors="coerce")
    d = d[(d["date"].dt.year == 2025) & d["province"].isin(PROV) & d["pairing"].isin(GOOD_PAIRING)
          & d["date_precision"].isin(PRECISION_DAYS)].copy()
    d["half_width_days"] = d["date_precision"].map(PRECISION_DAYS)
    d["num"] = pd.to_numeric(d["value"], errors="coerce")
    OUT.mkdir(parents=True, exist_ok=True)
    d.drop(columns=["context"], errors="ignore").to_csv(OUT / "labels_2025.csv", index=False)
    return d


def phenology(labels: pd.DataFrame, feats: dict[str, pd.DataFrame]) -> dict:
    rows = []
    f = labels[labels["metric"] == "phenology_stage"]
    for prov, fe in feats.items():
        g = fe.loc["2025-01-01":, "gdd_base9_1"].cumsum()
        hit = g[g >= FULL_FLOWERING_GDD]
        pred = hit.index[0] if len(hit) else pd.NaT
        reported = f[(f["province"] == prov) & (f["stage_code"] == "F")]["date"]
        if reported.empty or pd.isna(pred):
            rows.append({"province": prov, "predicted_full_flowering": str(pred.date()) if pd.notna(pred) else None,
                         "reported_F_first": None, "reported_F_last": None, "inside_window": None})
            continue
        lo, hi = reported.min(), reported.max()
        rows.append({"province": prov, "predicted_full_flowering": str(pred.date()),
                     "reported_F_first": str(lo.date()), "reported_F_last": str(hi.date()),
                     "days_outside_window": int(max((lo - pred).days, (pred - hi).days, 0)),
                     "inside_window": bool(lo - pd.Timedelta(days=15) <= pred <= hi + pd.Timedelta(days=15))})
    scored = [r for r in rows if r.get("inside_window") is not None]
    return {"assumption": "dormancy release = 1 Jan (chilling model not implemented); GDD threshold 495",
            "n_provinces": len(scored), "n_inside_window_pm15d": sum(r["inside_window"] for r in scored), "rows": rows}


def window_mean(fe: pd.DataFrame, col: str, end: pd.Timestamp, days: int) -> float:
    w = fe.loc[end - pd.Timedelta(days=days - 1): end, col]
    return float(w.sum()) if len(w) else np.nan


def lag_scan(labels: pd.DataFrame, feats: dict[str, pd.DataFrame], metrics: list[str], col: str,
             agg_days: int = 28, thresh: float | None = None) -> dict:
    """Spearman between label value and a trailing sum of a feature, scanning lags (weeks)."""
    d = labels[labels["metric"].isin(metrics)].dropna(subset=["num"])
    d = d.groupby(["province", "date"], as_index=False)["num"].mean()  # zones/sub-metrics -> province-date
    out = {"n_labels": len(d), "window_days": agg_days, "feature": col, "lags": []}
    for lag_w in (0, 2, 4, 6):
        xs, ys = [], []
        for _, r in d.iterrows():
            fe = feats[r["province"]]
            c = (fe[col] >= thresh).astype(float).to_frame(col) if thresh is not None else fe[[col]]
            x = window_mean(c, col, r["date"] - pd.Timedelta(weeks=lag_w), agg_days)
            if not np.isnan(x):
                xs.append(x)
                ys.append(r["num"])
        if len(xs) >= 8:
            rho, p = spearmanr(xs, ys)
            out["lags"].append({"lag_weeks": lag_w, "n": len(xs), "spearman": round(float(rho), 3), "p": round(float(p), 4)})
    best = max(out["lags"], key=lambda x: abs(x["spearman"])) if out["lags"] else None
    out["best"] = best
    return out


def main() -> None:
    feats = load_features()
    labels = clean_labels()
    res = {
        "n_labels_after_cleaning": len(labels),
        "provinces_with_features": list(feats),
        "phenology": phenology(labels, feats),
        "repilo_vs_wet_hours": lag_scan(labels, feats, ["repilo_leaf_pct", "repilo_plomizo_leaf_pct"], "wet_hours_8_24c"),
        "fly_punctured_vs_hot_days": lag_scan(
            labels, feats, ["fly_punctured_pct", "fly_punctured_total_pct", "fly_punctured_live_pct"], "tmax_c", thresh=35.0),
        "caveats": [
            "2025 only; RAIF dates are coarse (month / part-of-month), so +/- 5-15 day label error",
            "wet hours are an ERA5 proxy (RH>=90% or rain, 8-24 C), not measured leaf wetness",
            "labels are province means; ERA5 features are olive-area weighted province means",
            "no threshold was tuned; this reports agreement of the current rules/proxies only",
        ],
    }
    (OUT / "results.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
