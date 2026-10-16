"""Local dashboard for the data downloads (LPIS, ERA5, ground truth).

Usage: uv run python scripts/monitor.py [--port 8765]   then open http://localhost:8765
Reads only the filesystem + process list; changes nothing. Auto-refreshes every 5 s.
"""
import argparse
import json
import os
import subprocess
import sys
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
RAW = ROOT / "data/raw"
HIST: dict[str, deque] = {}  # key -> deque[(t, done, bytes)]
CACHE: dict = {"lpis_expected": None, "lpis_error": None}


def regions() -> list[dict]:
    import yaml
    return yaml.safe_load((ROOT / "configs/regions.yaml").read_text())["regions"]


def scan(base: Path, pattern: str):
    """-> (count, bytes, part_count, newest_mtime)"""
    n = b = parts = 0
    newest = 0.0
    if base.exists():
        for p in base.rglob(pattern):
            try:
                st = p.stat()
            except OSError:
                continue
            n += 1
            b += st.st_size
            newest = max(newest, st.st_mtime)
        parts = sum(1 for _ in base.rglob("*.part"))
    return n, b, parts, newest


def running(needle: str) -> bool:
    out = subprocess.run(["pgrep", "-f", needle], capture_output=True, text=True, check=False).stdout.split()
    return len([p for p in out if p]) > 0


def rate(key: str, done: int, nbytes: int):
    now = time.time()
    h = HIST.setdefault(key, deque(maxlen=400))
    if not h or now - h[-1][0] >= 5:
        h.append((now, done, nbytes))
    old = next((x for x in h if now - x[0] <= 300), h[0])
    dt = max(now - old[0], 1)
    return (done - old[1]) / dt * 60, (nbytes - old[2]) / dt  # files/min, bytes/s


def lpis_expected_worker():
    try:
        import download_lpis as d
        import yaml
        base = d.BASE.format(year="2026")
        pdirs = {}
        for href, _ in d.listing(base):
            import re
            m = re.match(r"(\d\d)%20-", href)
            if m:
                pdirs[m.group(1)] = href
        total = 0
        for reg in yaml.safe_load((ROOT / "configs/regions.yaml").read_text())["regions"]:
            for prov in reg["provinces"]:
                total += sum(1 for h, _ in d.listing(base + pdirs[prov]) if h.endswith("_gpkg.zip"))
        CACHE["lpis_expected"] = total
    except Exception as e:  # noqa: BLE001
        CACHE["lpis_error"] = str(e)


def status() -> dict:
    out: dict = {"time": time.time()}
    # LPIS
    n, b, parts, newest = scan(RAW / "lpis", "*.zip")
    exp = CACHE["lpis_expected"]
    fpm, bps = rate("lpis", n, b)
    per = []
    for r in regions():
        rn, rb, _, _ = scan(RAW / "lpis/2026" / r["id"], "*.zip")
        per.append({"region": r["name"], "files": rn, "bytes": rb})
    out["lpis"] = {"done": n, "expected": exp, "bytes": b, "partial": parts, "files_per_min": fpm,
                   "bytes_per_s": bps, "running": running("download_lpis.py"), "regions": per,
                   "last_write": newest, "error": CACHE["lpis_error"]}
    # ERA5
    try:
        import download_era5 as e
        jobs = list(e.jobs_for("olive", set(), e.span(os.environ.get("KAIROS_ERA5_YEARS", "2022-2025")), e.span("1-12")))
        jobs += list(e.jobs_for("olive", set(), [2021], e.span("10-12")))  # chilling window for campaign 2022
    except Exception as ex:  # noqa: BLE001
        jobs, out["era5_error"] = [], str(ex)
    expected: dict = {}
    for ds, _, dest in jobs:
        expected.setdefault((ds, dest.parent.name), 0)
        expected[(ds, dest.parent.name)] += 1
    n, b, parts, newest = scan(RAW / "climate", "*.nc")
    fpm, bps = rate("era5", n, b)
    rows = []
    for (ds, reg), tot in sorted(expected.items()):
        rn, rb, _, _ = scan(RAW / "climate" / ds / reg, "*.nc")
        rows.append({"dataset": ds, "region": reg, "done": rn, "expected": tot, "bytes": rb})
    out["era5"] = {"done": n, "expected": len(jobs), "bytes": b, "inflight": parts,
                   "files_per_min": fpm, "bytes_per_s": bps, "running": running("download_era5.py"),
                   "rows": rows, "last_write": newest}
    # ground truth
    gt = []
    for name, pat in [("RAIF reports", "raif/*"), ("SIAR daily", "siar/*")]:
        d = RAW / "ground_truth"
        cnt = sum(1 for p in d.glob(pat) if p.is_file()) if d.exists() else 0
        gt.append({"name": name, "files": cnt})
    out["ground_truth"] = gt
    out["disk_free_gb"] = round(__import__("shutil").disk_usage(ROOT).free / 1e9, 1)
    return out


PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Kairos Downloads</title>
<style>
:root{--bg:#f7f7f5;--card:#fff;--fg:#1d1d1b;--mut:#6b6b66;--line:#e4e4df;--ok:#2f7d4f;--warn:#b7791f;--bar:#3b6fb6;--track:#ececE6}
@media (prefers-color-scheme:dark){:root{--bg:#161614;--card:#201f1d;--fg:#ecebe6;--mut:#9a9a92;--line:#34332f;--ok:#58b57e;--warn:#e0a94a;--bar:#6b9ce0;--track:#34332f}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,sans-serif;padding:24px 16px}
main{max-width:980px;margin:auto}h1{font-size:20px;margin:0 0 4px}.sub{color:var(--mut);margin-bottom:20px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;margin-bottom:16px}
.head{display:flex;justify-content:space-between;align-items:baseline;gap:8px;flex-wrap:wrap}h2{font-size:15px;margin:0}
.pill{font-size:12px;padding:2px 8px;border-radius:99px;border:1px solid var(--line)}.on{color:var(--ok);border-color:var(--ok)}.off{color:var(--warn);border-color:var(--warn)}
.track{height:10px;background:var(--track);border-radius:6px;overflow:hidden;margin:10px 0 6px}.fill{height:100%;background:var(--bar);transition:width .5s}
.stats{display:flex;gap:20px;flex-wrap:wrap;color:var(--mut)}.stats b{color:var(--fg);font-weight:600}
table{width:100%;border-collapse:collapse;margin-top:10px;font-size:13px}th,td{text-align:left;padding:6px 4px;border-top:1px solid var(--line)}th{color:var(--mut);font-weight:500}
td.num{text-align:right;font-variant-numeric:tabular-nums}.mini{width:90px}.mini .track{margin:0;height:6px}
</style></head><body><main><h1>Kairos data downloads</h1><div class="sub" id="upd">loading…</div><div id="app"></div></main>
<script>
const f=(n)=>n==null?'–':n.toLocaleString();
const gb=(b)=>b>=1e9?(b/1e9).toFixed(2)+' GB':(b/1e6).toFixed(0)+' MB';
const pct=(a,b)=>b?Math.min(100,100*a/b):0;
function eta(done,exp,fpm){if(!exp||!fpm||fpm<=0)return '–';const m=(exp-done)/fpm;return m>=120?(m/60).toFixed(1)+' h':Math.round(m)+' min'}
function bar(a,b){return `<div class="track"><div class="fill" style="width:${pct(a,b)}%"></div></div>`}
function pill(on){return `<span class="pill ${on?'on':'off'}">${on?'running':'not running'}</span>`}
function card(title,d,extra){return `<div class="card"><div class="head"><h2>${title}</h2>${pill(d.running)}</div>
${bar(d.done,d.expected)}<div class="stats"><span><b>${f(d.done)}</b> / ${f(d.expected)} files (${pct(d.done,d.expected).toFixed(1)}%)</span>
<span><b>${gb(d.bytes)}</b> on disk</span><span><b>${d.files_per_min.toFixed(1)}</b> files/min (5 min avg)</span>
<span>ETA <b>${eta(d.done,d.expected,d.files_per_min)}</b></span>${extra||''}</div></div>`}
async function tick(){
 try{const s=await (await fetch('/api/status')).json();
 const l=s.lpis,e=s.era5;
 let h=card('LPIS · SIGPAC recintos 2026 (FEGA)',l,`<span>in progress: <b>${l.partial}</b></span>`);
 h=h.replace('</div></div>','</div>'+`<table><tr><th>Region</th><th class="num">Files</th><th class="num">Size</th></tr>`+
  l.regions.map(r=>`<tr><td>${r.region}</td><td class="num">${f(r.files)}</td><td class="num">${gb(r.bytes)}</td></tr>`).join('')+'</table></div>');
 let eh=card('ERA5 / ERA5-Land · hourly, Oct 2021 – 2025',e,`<span>CDS jobs in flight: <b>${e.inflight}</b></span>`);
 eh=eh.replace('</div></div>','</div>'+`<table><tr><th>Dataset</th><th>Region</th><th class="mini"></th><th class="num">Done</th><th class="num">Size</th></tr>`+
  e.rows.map(r=>`<tr><td>${r.dataset.replace('reanalysis-','')}</td><td>${r.region}</td><td class="mini">${bar(r.done,r.expected)}</td><td class="num">${r.done}/${r.expected}</td><td class="num">${gb(r.bytes)}</td></tr>`).join('')+'</table></div>');
 const g=`<div class="card"><h2>Ground truth</h2><table>`+s.ground_truth.map(x=>`<tr><td>${x.name}</td><td class="num">${x.files} files</td></tr>`).join('')+`</table></div>`;
 document.getElementById('app').innerHTML=h+eh+g;
 document.getElementById('upd').textContent='Updated '+new Date(s.time*1000).toLocaleTimeString()+' · disk free '+s.disk_free_gb+' GB · refreshes every 5 s'+(l.error?' · LPIS total unavailable: '+l.error:'');
 }catch(err){document.getElementById('upd').textContent='Cannot reach monitor: '+err}
}
tick();setInterval(tick,5000);
</script></body></html>"""


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/status"):
            body, ctype = json.dumps(status()).encode(), "application/json"
        else:
            body, ctype = PAGE.encode(), "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()
    threading.Thread(target=lpis_expected_worker, daemon=True).start()
    print(f"Dashboard: http://localhost:{a.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", a.port), H).serve_forever()


if __name__ == "__main__":
    main()
