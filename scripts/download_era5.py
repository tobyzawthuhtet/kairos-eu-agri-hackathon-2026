"""Download ERA5 / ERA5-Land hourly data for the union bounding box of all target regions via the CDS API.

One request per dataset per month over a single Spain-wide box (CDS cost is driven by fields x time, not area,
so one box is ~5x cheaper than one request per region). Per-region/province slicing is done later.
Requested variables come from the decision table: every `climate` driver in
configs/crops/<crop>/decision_table.csv is looked up in configs/variable_catalog.yaml (+ catalog `extras`).
Credentials: ~/.cdsapirc (never in the repo).

Usage: uv run python scripts/download_era5.py --crop olive --start 2021-10 --end 2025-12 [--workers 3] [--dry-run]
Output: data/raw/climate/<dataset>/spain/<year>-<month>_g<i>.nc  (resumable; rejected/queue-limited requests are retried)
"""
import argparse
import csv
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
AREA = "spain"


def span(s: str) -> list[int]:
    a, _, b = s.partition("-")
    return list(range(int(a), int(b or a) + 1))


def union_bbox() -> tuple[float, float, float, float]:
    regs = yaml.safe_load((ROOT / "configs/regions.yaml").read_text())["regions"]
    return (min(r["bbox"][0] for r in regs), min(r["bbox"][1] for r in regs),
            max(r["bbox"][2] for r in regs), max(r["bbox"][3] for r in regs))


def jobs_for(crop, regions, years, months, chunk: int = 3):
    """`regions` is kept for call compatibility; data is downloaded for the union box."""
    full = yaml.safe_load((ROOT / "configs/variable_catalog.yaml").read_text())
    cat = {d["id"]: d for d in full["drivers"]}
    with open(ROOT / f"configs/crops/{crop}/decision_table.csv", newline="") as f:
        drivers = sorted({r["driver"] for r in csv.DictReader(f) if r["data_class"] == "climate"})
    by_ds: dict[str, list[str]] = {}
    for e in [cat[d]["era5"] for d in drivers] + [x["era5"] for x in full.get("extras", [])]:
        by_ds.setdefault(e["dataset"], [])
        by_ds[e["dataset"]] += [v for v in e["variables"] if v not in by_ds[e["dataset"]]]
    w, s, e, n = union_bbox()
    for dataset, allvars in by_ds.items():
        # split variables into small groups: the CDS cost limit rejects large Spain-wide requests
        for gi, i in enumerate(range(0, len(allvars), chunk)):
            variables = allvars[i:i + chunk]
            for y in years:
                for m in months:
                    dest = ROOT / "data/raw/climate" / dataset / AREA / f"{y}-{m:02d}_g{gi}.nc"
                    req = {
                        "variable": variables,
                        "year": str(y),
                        "month": f"{m:02d}",
                        "day": [f"{d:02d}" for d in range(1, 32)],
                        "time": [f"{h:02d}:00" for h in range(24)],
                        "area": [n, w, s, e],  # CDS order: N, W, S, E
                        "data_format": "netcdf",
                        "download_format": "unarchived",
                    }
                    if dataset == "reanalysis-era5-single-levels":
                        req["product_type"] = ["reanalysis"]  # required for single-levels, absent in -land
                    yield dataset, req, dest


def run(job, retries: int = 40) -> str:
    import cdsapi

    dataset, req, dest = job
    if dest.exists() and dest.stat().st_size > 0:
        return "skip"
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    for attempt in range(retries):
        try:
            cdsapi.Client(quiet=True, wait_until_complete=True).retrieve(dataset, req, str(tmp))
            tmp.rename(dest)
            return "ok"
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            if "temporarily limited" in msg or "rejected" in msg:  # queue limit: back off and retry
                time.sleep(min(60 * (attempt + 1), 600))
                continue
            return f"fail {dest.name}: {msg[:300]}"
    return f"fail {dest.name}: gave up after {retries} queue-limit retries"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--crop", default="olive")
    ap.add_argument("--start", default="2021-10", help="YYYY-MM (Oct 2021 = chilling window of campaign 2022)")
    ap.add_argument("--end", default="2025-12")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--chunk", type=int, default=3, help="variables per request")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    pairs = [(p.year, p.month) for p in pd.period_range(a.start, a.end, freq="M")]
    jobs = [j for y, m in pairs for j in jobs_for(a.crop, set(), [y], [m], a.chunk)]
    print(f"{len(jobs)} requests, area {AREA} {union_bbox()}", flush=True)
    if a.dry_run:
        return
    fails = 0
    with ThreadPoolExecutor(a.workers) as ex:
        for i, res in enumerate(ex.map(run, jobs), 1):
            if res.startswith("fail"):
                fails += 1
                print(res, file=sys.stderr, flush=True)
            if i % 5 == 0:
                print(f"{i}/{len(jobs)}", flush=True)
    print(f"done, {fails} failures")


if __name__ == "__main__":
    main()
