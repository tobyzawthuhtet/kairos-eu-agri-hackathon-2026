"""Aggregate downloaded SIGPAC GPKGs into olive-area weights per ERA5 grid cell and province.

Usage: uv run python scripts/build_olive_weights.py
Reads  data/raw/lpis/2026/<region>/<prov>/*_gpkg.zip  (whatever is downloaded so far; re-runnable)
Writes data/processed/olive_weights.csv  (region, province, lat, lon, olive_ha)
Per-zip results are cached in data/interim/olive_cells/ so reruns only process new files.
"""
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from kairos.features.olive_mask import zip_to_cells

CACHE = ROOT / "data/interim/olive_cells"


def work(zp: Path) -> Path:
    region = zp.parents[1].name
    cp = CACHE / region / (zp.stem + ".csv")
    if not cp.exists():
        cp.parent.mkdir(parents=True, exist_ok=True)
        zip_to_cells(zp).to_csv(cp, index=False)
    return cp


def main() -> None:
    zips = sorted((ROOT / "data/raw/lpis/2026").glob("*/*/*_gpkg.zip"))
    print(f"{len(zips)} municipality files", flush=True)
    with ProcessPoolExecutor(4) as ex:
        paths = list(ex.map(work, zips, chunksize=8))
    parts = []
    for cp in paths:
        df = pd.read_csv(cp, dtype={"province": str})
        df["region"] = cp.parent.name
        parts.append(df)
    allc = pd.concat(parts)
    w = allc.groupby(["region", "province", "lat", "lon"], as_index=False)["olive_ha"].sum()
    dest = ROOT / "data/processed/olive_weights.csv"
    w.to_csv(dest, index=False)
    print(w.groupby(["region", "province"])["olive_ha"].sum().round(0).to_string())


if __name__ == "__main__":
    main()
