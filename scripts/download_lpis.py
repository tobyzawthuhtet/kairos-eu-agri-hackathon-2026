"""Download Spanish LPIS (SIGPAC recintos) GeoPackages from the FEGA ATOM service.

One zip per municipality, grouped by province. Resumable: existing files of the right size are skipped.
Usage: uv run python scripts/download_lpis.py [--year 2026] [--regions andalucia,extremadura] [--workers 8]
Output: data/raw/lpis/<year>/<region_id>/<province>/<file>.zip
"""
import argparse
import re
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://www.fega.gob.es/atom/{year}/rec_{year}/"


def get(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()


def listing(url: str) -> list[tuple[str, int | None]]:
    html = get(url).decode("utf-8", "replace")
    mult = {"K": 1e3, "M": 1e6, "G": 1e9}
    out = []
    for m in re.finditer(r'<a href="([^"?/][^"]*)">[^<]*</a></td><td[^>]*>[^<]*</td><td[^>]*>\s*([\d.]+)?([KMG])?', html):
        out.append((m.group(1), int(float(m.group(2)) * mult.get(m.group(3), 1)) if m.group(2) else None))
    return out


def fetch(job: tuple[str, Path]) -> str:
    url, dest = job
    if dest.exists() and dest.stat().st_size > 0:
        return "skip"
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    try:
        with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)
        tmp.rename(dest)
        return "ok"
    except Exception as e:  # noqa: BLE001
        return f"fail {url}: {e}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", default="2026")
    ap.add_argument("--regions", default="")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    base = BASE.format(year=a.year)
    cfg = yaml.safe_load((ROOT / "configs" / "regions.yaml").read_text())["regions"]
    want = set(filter(None, a.regions.split(",")))
    pdirs = {}
    for href, _ in listing(base):
        m = re.match(r"(\d\d)%20-", href)
        if m:
            pdirs[m.group(1)] = href

    jobs = []
    for reg in cfg:
        if want and reg["id"] not in want:
            continue
        for prov in reg["provinces"]:
            purl = base + pdirs[prov]
            for href, _ in listing(purl):
                if href.endswith("_gpkg.zip"):
                    name = urllib.parse.unquote(href)
                    jobs.append((purl + href, ROOT / "data/raw/lpis" / a.year / reg["id"] / prov / name))
    print(f"{len(jobs)} files", flush=True)
    if a.dry_run:
        return
    fails = 0
    with ThreadPoolExecutor(a.workers) as ex:
        for i, res in enumerate(ex.map(fetch, jobs), 1):
            if res.startswith("fail"):
                fails += 1
                print(res, file=sys.stderr, flush=True)
            if i % 100 == 0:
                print(f"{i}/{len(jobs)}", flush=True)
    print(f"done, {fails} failures")


if __name__ == "__main__":
    main()
