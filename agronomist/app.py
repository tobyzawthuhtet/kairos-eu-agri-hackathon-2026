"""Kairos agronomist review tool (Flask): read each decision-table scenario in plain language, then approve, change or reject it.

Run: `uv run python agronomist/app.py` (port 5050). Reviews are saved to data/processed/agronomist/reviews.json and are read by the
rule engine, so approving a scenario marks it validated in the farmer app, advisor app and dashboard, and rejecting it stops it firing.
"""
import csv
import io
import re
import sys
from functools import lru_cache
from pathlib import Path

import pandas as pd
from flask import (
    Flask,
    Response,
    abort,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)

sys.path.insert(0, str(Path(__file__).parent))
import figures
import plain

from kairos.rules import reviews
from kairos.rules.table_engine import evaluate, load_ruleset
from kairos.serving import replay

ROOT = Path(__file__).resolve().parents[1]
CROPS_DIR = ROOT / "configs/crops"
STATUS_LABEL = {"none": "Not reviewed", "approved": "Approved", "modified": "Approved with changes", "rejected": "Rejected", "unsure": "Needs a field check"}
app = Flask(__name__)


def current_crop() -> str:
    crop = request.args.get("crop") or request.cookies.get("crop") or "olive"
    return crop if crop in figures.crops() else "olive"


@lru_cache
def _table(crop: str) -> pd.DataFrame:
    return pd.read_csv(CROPS_DIR / crop / "decision_table.csv", dtype=str).fillna("")


def table() -> pd.DataFrame:
    return _table(current_crop())


@app.context_processor
def inject_crop():
    return {"crop": current_crop(), "crops": figures.crops(), "weather_ok": figures.has_weather(current_crop())}


def scenarios() -> list[dict]:
    rows = table().to_dict("records")
    rv = reviews.load()
    ne = {x["rule_id"]: x["reason"] for x in load_ruleset(current_crop()).not_evaluable}
    fired = fire_counts(reviews.mtime())
    out = []
    for r in rows:
        sid = r["scenario_id"]
        rev = rv.get(sid)
        r["sev"] = plain.SEV.get(r["severity"].strip().lower(), r["severity"])
        r["conf"] = plain.CONF.get(r["confidence"].strip().lower(), r["confidence"] or "unrated")
        r["stage_name"] = plain.STAGE.get(r["stage"].split("|")[0], r["stage"])
        r["stage_idx"] = plain.STAGE_ORDER.index(r["stage"].split("|")[0]) if r["stage"].split("|")[0] in plain.STAGE_ORDER else 99
        r["review"] = rev
        r["status"] = rev["status"] if rev else "none"
        r["sentence"] = plain.sentence(r, rev["threshold"] if rev and rev.get("threshold") else None)
        r["duration_nice"] = "Not given in the sources" if r["duration"] in ("", "NAV") else r["duration"].replace("NAV", "not given")
        r["regions_nice"] = re.sub(r"\s*[|;]\s*", ", ", r["regions"]) or "Not specified"
        r["unit_nice"] = plain.unit(r["unit"]).strip()
        r["why_not_checked"] = ne.get(sid)
        r["checked_by_weather"] = sid not in ne
        r["fired"] = fired.get(sid)
        out.append(r)
    return out


@lru_cache
def fire_counts(_mtime: float) -> dict[str, dict]:
    """How often each weather scenario would have fired in 2025 across the province series (a sensitivity check)."""
    res: dict[str, dict] = {}
    for code, df in replay.features().items():
        a = evaluate(df, replay.province_meta()[code]["region"])
        if a.empty:
            continue
        for rid, g in a.groupby("rule_id"):
            e = res.setdefault(rid, {"days": 0, "provinces": 0})
            e["days"] += len(g)
            e["provinces"] += 1
    return res


def counts(rows: list[dict]) -> dict:
    c = {k: 0 for k in STATUS_LABEL}
    for r in rows:
        c[r["status"]] += 1
    return c


@app.route("/")
def index():
    rows = scenarios()
    q, stage, status, hazard, check = (request.args.get(k, "") for k in ("q", "stage", "status", "hazard", "check"))
    shown = [r for r in rows if (not stage or r["stage"].split("|")[0] == stage) and (not status or r["status"] == status) and (not hazard or r["hazard"] == hazard)
             and (not check or (check == "weather") == r["checked_by_weather"]) and (not q or q.lower() in f"{r['scenario_id']} {r['hazard']} {r['sentence']} {r['action']}".lower())]
    shown.sort(key=lambda r: (r["stage_idx"], r["hazard"], r["scenario_id"]))
    groups: dict[str, list] = {}
    for r in shown:
        groups.setdefault(r["stage_name"], []).append(r)
    nxt = next((r for r in shown if r["status"] == "none"), None)
    return render_template("index.html", groups=groups, c=counts(rows), total=len(rows), shown=len(shown), hazards=sorted({r["hazard"] for r in rows}), stages=plain.STAGE,
                           f={"q": q, "stage": stage, "status": status, "hazard": hazard, "check": check}, status_label=STATUS_LABEL, next_id=nxt["scenario_id"] if nxt else None,
                           reviewer=request.cookies.get("reviewer", ""))


@app.route("/scenario/<sid>", methods=["GET", "POST"])
def scenario(sid: str):
    rows = scenarios()
    r = next((x for x in rows if x["scenario_id"] == sid), None)
    if r is None:
        abort(404)
    if request.method == "POST":
        status = request.form.get("decision", "")
        if status not in reviews.STATUSES:
            abort(400)
        who = request.form.get("reviewer", "").strip() or "agronomist"
        thr = request.form.get("threshold", "").strip()
        act = request.form.get("action", "").strip()
        changed_thr = thr and thr != r["threshold"]
        changed_act = act and act != r["action"]
        if status == "modified" and not (changed_thr or changed_act or request.form.get("duration", "").strip()):
            status = "approved"
        reviews.save_review(sid, status, who, request.form.get("comment", "").strip(), thr if changed_thr else None, act if changed_act else None,
                            request.form.get("duration", "").strip() or None, original={"threshold": r["threshold"], "action": r["action"], "duration": r["duration"]})
        nxt = next((x for x in scenarios() if x["status"] == "none" and x["scenario_id"] != sid), None)
        resp = make_response(redirect(url_for("scenario", sid=nxt["scenario_id"], saved=sid) if nxt and request.form.get("go_next") else url_for("scenario", sid=sid, saved=sid)))
        resp.set_cookie("reviewer", who, max_age=86400 * 365)
        return resp
    idx = [x["scenario_id"] for x in rows]
    order = sorted(rows, key=lambda x: (x["stage_idx"], x["hazard"], x["scenario_id"]))
    pos = [x["scenario_id"] for x in order].index(sid)
    src = r["source_url"]
    return render_template("scenario.html", r=r, c=counts(rows), total=len(rows), status_label=STATUS_LABEL, reviewer=request.cookies.get("reviewer", ""), saved=request.args.get("saved"),
                           prev_id=order[pos - 1]["scenario_id"] if pos else None, next_id=order[pos + 1]["scenario_id"] if pos + 1 < len(order) else None, pos=pos + 1, n=len(idx),
                           src=src if re.match(r"^https?://", src or "") else None)


@app.route("/overview")
def overview():
    rows = scenarios()
    return render_template("overview.html", c=counts(rows), total=len(rows), status_label=STATUS_LABEL)


@app.route("/api/overview")
def api_overview():
    rows = scenarios()
    by_stage: dict[str, dict] = {}
    for r in rows:
        e = by_stage.setdefault(r["stage_name"], {k: 0 for k in STATUS_LABEL})
        e[r["status"]] += 1
    out = figures.overview(current_crop())
    out["progress"] = by_stage
    out["sentences"] = {r["scenario_id"]: r["sentence"] for r in rows}
    out["stage_labels"] = plain.STAGE
    out["stage_order"] = [k for k in plain.STAGE_ORDER if k in out["stages"]] or list(out["stages"])
    return jsonify(out)


@app.route("/api/scenario/<sid>/series")
def api_series(sid: str):
    s = figures.series(current_crop(), sid)
    if s is None:
        return jsonify({"error": "This scenario cannot be tested from weather data."}), 404
    return jsonify(s)


@app.route("/crop/<name>")
def set_crop(name: str):
    resp = make_response(redirect(url_for("index")))
    if name in figures.crops():
        resp.set_cookie("crop", name, max_age=86400 * 365)
    return resp


@app.route("/export.csv")
def export():
    rv = reviews.load()
    buf = io.StringIO()
    cols = [*table().columns, "review_status", "reviewer", "reviewed_at", "reviewed_threshold", "reviewed_action", "reviewed_duration", "reviewer_comment"]
    w = csv.DictWriter(buf, fieldnames=cols)
    w.writeheader()
    for r in table().to_dict("records"):
        e = rv.get(r["scenario_id"], {})
        w.writerow({**r, "review_status": e.get("status", "not reviewed"), "reviewer": e.get("reviewer", ""), "reviewed_at": e.get("at", ""), "reviewed_threshold": e.get("threshold") or "",
                    "reviewed_action": e.get("action") or "", "reviewed_duration": e.get("duration") or "", "reviewer_comment": e.get("comment", "")})
    return Response(buf.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=olive_scenarios_reviewed.csv"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)
