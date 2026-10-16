"""Build olive-weighted daily climate features per province from downloaded ERA5 files.

Usage: uv run python scripts/build_features.py [--regions andalucia] [--years 2022-2025]
Needs data/processed/olive_weights.csv (scripts/build_olive_weights.py).
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


def month_files(base: Path, region: str, tag: str, ym: str) -> Path | None:
    p = base / region / f"{tag}{ym}.nc"
    return p if p.exists() else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--regions", default="")
    ap.add_argument("--start", default="2021-10")
    ap.add_argument("--end", default="2025-12")
    a = ap.parse_args()
    weights = pd.read_csv(ROOT / "data/processed/olive_weights.csv", dtype={"province": str})
    months = pd.period_range(a.start, a.end, freq="M").astype(str)
    (ROOT / "data/processed/features").mkdir(parents=True, exist_ok=True)
    for region, wr in weights.groupby("region"):
        if a.regions and region not in a.regions.split(","):
            continue
        frames: dict[str, list[pd.DataFrame]] = {p: [] for p in wr["province"].unique()}
        for ym in months:
            f = month_files(LAND, region, "", ym)
            if f is None:
                continue
            pe, gu = month_files(LAND, region, "pev_", ym), month_files(SL, region, "", ym)
            with xr.open_dataset(f) as ds:
                pev = xr.open_dataset(pe) if pe else None
                gust = xr.open_dataset(gu) if gu else None
                cells = daily_cell_features(ds, gust=gust, pev=pev).load()
            for prov, wp in wr.groupby("province"):
                frames[prov].append(province_series(cells, wp))
        for prov, fr in frames.items():
            if fr:
                pd.concat(fr).sort_index().to_csv(ROOT / f"data/processed/features/{region}_{prov}.csv")
                print(region, prov, sum(len(x) for x in fr), "days")


if __name__ == "__main__":
    main()
