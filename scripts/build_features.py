"""Build olive-weighted daily climate features per province from downloaded ERA5 files.

Usage: uv run python scripts/build_features.py [--regions andalucia] [--years 2022-2025]
Reads data/raw/climate/*/spain/<YYYY-MM>.nc. Needs data/processed/olive_weights.csv (scripts/build_olive_weights.py).
Writes data/processed/features/<region>_<province>.csv
"""
import argparse
import sys
from pathlib import Path

import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from kairos.features.era5_features import daily_cell_features, province_series

LAND = ROOT / "data/raw/climate/reanalysis-era5-land"
SL = ROOT / "data/raw/climate/reanalysis-era5-single-levels"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--regions", default="")
    ap.add_argument("--start", default="2021-10")
    ap.add_argument("--end", default="2025-12")
    a = ap.parse_args()
    weights = pd.read_csv(ROOT / "data/processed/olive_weights.csv", dtype={"province": str})
    if a.regions:
        weights = weights[weights["region"].isin(a.regions.split(","))]
    frames: dict[tuple[str, str], list[pd.DataFrame]] = {}
    for ym in pd.period_range(a.start, a.end, freq="M").astype(str):
        f = LAND / "spain" / f"{ym}.nc"
        if not f.exists():
            continue
        g = SL / "spain" / f"{ym}.nc"
        with xr.open_dataset(f) as ds:
            gust = xr.open_dataset(g) if g.exists() else None
            pev = ds if "pev" in ds else None
            cells = daily_cell_features(ds, gust=gust, pev=pev).load()
        for (region, prov), wp in weights.groupby(["region", "province"]):
            frames.setdefault((region, prov), []).append(province_series(cells, wp))
        print(ym, flush=True)
    out = ROOT / "data/processed/features"
    out.mkdir(parents=True, exist_ok=True)
    for (region, prov), fr in frames.items():
        pd.concat(fr).sort_index().to_csv(out / f"{region}_{prov}.csv")
        print(region, prov, sum(len(x) for x in fr), "days")


if __name__ == "__main__":
    main()
