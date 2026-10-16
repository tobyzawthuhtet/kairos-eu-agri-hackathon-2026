"""Download ERA5 / ERA5-Land hourly data per region bounding box via the CDS API.

Requested variables are derived from the decision table: every `climate` driver in
configs/crops/<crop>/decision_table.csv is looked up in configs/variable_catalog.yaml.
Credentials: ~/.cdsapirc (never in the repo).

Usage: uv run python scripts/download_era5.py --crop olive --years 2015-2025 [--regions extremadura]
       [--months 1-12] [--workers 3] [--dry-run]
Output: data/raw/climate/<dataset>/<region>/<year>-<month>.nc  (resumable)
"""
import argparse
import csv
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def span(s: str) -> list[int]:
    a, _, b = s.partition("-")
    return list(range(int(a), int(b or a) + 1))


def jobs_for(crop, regions, years, months, only_tag=None):
    full = yaml.safe_load((ROOT / "configs/variable_catalog.yaml").read_text())
    cat = {d["id"]: d for d in full["drivers"]}
    with open(ROOT / f"configs/crops/{crop}/decision_table.csv", newline="") as f:
        drivers = sorted({r["driver"] for r in csv.DictReader(f) if r["data_class"] == "climate"})
    # one request per dataset/region/month: union of the variables all needed drivers share
    by_ds: dict[str, list[str]] = {}
    for drv in ([] if only_tag else drivers):
        e = cat[drv]["era5"]
        by_ds.setdefault(e["dataset"], [])
        by_ds[e["dataset"]] += [v for v in e["variables"] if v not in by_ds[e["dataset"]]]
    extras = [(x["tag"], x["era5"]) for x in full.get("extras", []) if not only_tag or x["tag"] == only_tag]
    regs = yaml.safe_load((ROOT / "configs/regions.yaml").read_text())["regions"]
    for reg in regs:
        if regions and reg["id"] not in regions:
            continue
        w, s, e, n = reg["bbox"]
        groups = [("", ds, v) for ds, v in by_ds.items()] + [(t, e["dataset"], e["variables"]) for t, e in extras]
        for tag, dataset, variables in groups:
            for y in years:
                for m in months:
                    dest = ROOT / "data/raw/climate" / dataset / reg["id"] / f"{tag + '_' if tag else ''}{y}-{m:02d}.nc"
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
                    yield dataset, req, dest


def run(job) -> str:
    import cdsapi

    dataset, req, dest = job
    if dest.exists() and dest.stat().st_size > 0:
        return "skip"
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    try:
        cdsapi.Client(quiet=True).retrieve(dataset, req, str(tmp))
        tmp.rename(dest)
        return "ok"
    except Exception as e:  # noqa: BLE001
        return f"fail {dest.name}: {e}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--crop", default="olive")
    ap.add_argument("--years", default="2022-2025")
    ap.add_argument("--months", default="1-12")
    ap.add_argument("--regions", default="")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--only-tag", default=None, help="only extra group, e.g. pev")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    jobs = list(jobs_for(a.crop, set(filter(None, a.regions.split(","))), span(a.years), span(a.months), a.only_tag))
    print(f"{len(jobs)} requests", flush=True)
    if a.dry_run:
        return
    fails = 0
    with ThreadPoolExecutor(a.workers) as ex:
        for i, res in enumerate(ex.map(run, jobs), 1):
            if res.startswith("fail"):
                fails += 1
                print(res, file=sys.stderr, flush=True)
            if i % 10 == 0:
                print(f"{i}/{len(jobs)}", flush=True)
    print(f"done, {fails} failures")


if __name__ == "__main__":
    main()
