"""Demo back end shared by the farmer app, the advisor app and the advisor dashboard.

Real inputs: LPIS plots (geometry, area, SIGPAC ref), ERA5-Land daily features per plot cell, the decision table.
Demo inputs: grower / farm names, varieties unless an external dataset is joined, the simulated irrigation log,
the seeded requests and reports. Replay: "tomorrow" and "forecast" are the actual following days of 2025.
"""
import hashlib
import json
import math
import threading
import time
from datetime import UTC, date, datetime, timedelta
from functools import lru_cache
from pathlib import Path

import pandas as pd
import yaml

from kairos.config import CONFIG_DIR
from kairos.demo.copy import KIND, SEV_UI, SUMMARY, TITLE
from kairos.rules import reviews
from kairos.rules.table_engine import (
    SEVERITY_RANK,
    active_stages,
    evaluate,
    load_ruleset,
    top_per_hazard,
)

ROOT = Path(__file__).resolve().parents[3]
DEMO = ROOT / "data/processed/demo"
STATE_FILE = DEMO / "state.json"
LOCK = threading.RLock()
DEFAULT_CLOCK = "2025-10-24"  # a Friday: real soil-drying alert, rain ahead in the replay
ETC_KC = 0.55  # olive crop factor applied to ERA5 reference evaporation (assumption)
STAGE_NAME = {"dormancy_chilling": "dormancy", "budbreak_shoot_growth": "bud break", "inflorescence_development": "flower buds",
              "flowering_anthesis": "flowering", "fruit_set": "fruit set", "pit_hardening": "pit hardening",
              "fruit_growth_oil_accumulation": "fruit growth", "ripening_harvest": "ripening and harvest", "post_harvest_recovery": "post-harvest"}
CONF = {"high": "High confidence", "medium": "Medium confidence", "low": "Low confidence"}
KINDS = ["Disease", "Pest", "Irrigation fault", "Weather damage"]


# ---------- static data ----------
@lru_cache
def doc() -> dict:
    return json.loads((DEMO / "farms.json").read_text())


def advisor() -> dict:
    return doc()["advisor"]


def farmers() -> list[dict]:
    return doc()["farmers"]


@lru_cache
def farmer_index() -> dict[str, dict]:
    return {f["id"]: f for f in farmers()}


@lru_cache
def parcel_index() -> dict[str, tuple[dict, dict]]:
    return {p["id"]: (f, p) for f in farmers() for p in f["parcels"]}


@lru_cache
def cells() -> dict[tuple, pd.DataFrame]:
    df = pd.read_csv(DEMO / "cell_features.csv.gz", parse_dates=["date"])
    return {(round(k[0], 1), round(k[1], 1)): g.set_index("date").sort_index() for k, g in df.groupby(["cell_lat", "cell_lon"])}


def cell_of(parcel: dict) -> pd.DataFrame:
    return cells()[(parcel["cell"][0], parcel["cell"][1])]


@lru_cache
def cell_table_alerts(lat: float, lon: float, _reviews_mtime: float = 0.0) -> pd.DataFrame:
    return top_per_hazard(evaluate(cells()[(lat, lon)], "andalucia"))


@lru_cache
def water_cfg() -> dict:
    return yaml.safe_load((CONFIG_DIR / "crops/olive/water_rules.yaml").read_text())


def date_range() -> tuple[str, str]:
    idx = next(iter(cells().values())).index
    return str(idx.min().date()), str(idx.max().date())


# ---------- helpers ----------
def _h(s: str) -> int:
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)


def _time(alert_id: str) -> str:
    n = 360 + _h(alert_id) % 780  # 06:00-19:00
    return f"{n // 60:02d}:{n % 60:02d}"


def _num(v):
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else float(v)


def _weekday(d: pd.Timestamp) -> str:
    return d.strftime("%A")


def km(a: list, b: list) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (a[1], a[0], b[1], b[0]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def _next_days(frame: pd.DataFrame, d: pd.Timestamp, n: int) -> pd.DataFrame:
    return frame.loc[d + timedelta(days=1): d + timedelta(days=n)]


def _forecast_line(frame: pd.DataFrame, d: pd.Timestamp, n: int) -> str:
    nx = _next_days(frame, d, n)
    if nx.empty:
        return "No later days in the replay."
    rain = nx["precip_mm"]
    wet = rain[rain >= 2.0]
    span = f"{nx['tmin_c'].min():.0f} to {nx['tmax_c'].max():.0f} °C"
    if wet.empty:
        return f"dry for the next {len(nx)} days, {span}"
    first = wet.index[0]
    return f"dry until {_weekday(first)}, {span}, then {rain.loc[first:].sum():.0f} mm rain" if first > nx.index[0] else f"rain from {_weekday(first)}: {wet.sum():.0f} mm, {span}"


# ---------- alerts ----------
def _alert(base_id: str, d: pd.Timestamp, farmer: dict, parcel: dict | None, hazard: str, severity: str, **kw) -> dict:
    aid = f"{base_id}|{d.date()}"
    sub = (f"{parcel['variety']} · {parcel['ha']:g} ha · {parcel['irrigation']}" if parcel else kw.pop("subtitle", "All parcels"))
    kw.pop("subtitle", None)
    return {"id": aid, "date": str(d.date()), "time": _time(aid), "farmer_id": farmer["id"], "parcel_id": parcel["id"] if parcel else None,
            "parcel_name": parcel["name"] if parcel else None, "hazard": hazard, "kind": KIND.get(hazard, "weather"),
            "severity": severity, "severity_ui": SEV_UI[severity], "subtitle": sub, **kw}


def _table_alert(row, d, farmer, parcel, frame) -> dict:
    steps = [s.strip().rstrip(".") for s in str(row.action).replace("\n", " ").split(";") if s.strip()]
    steps = [s[0].upper() + s[1:] + "." for s in steps][:4]
    hazard = row.hazard
    title = TITLE.get(hazard, hazard.replace("_", " ").capitalize() + " at {plot}").format(plot=parcel["name"])
    value = row.value
    summ = SUMMARY.get(hazard, "Reading {value:g} ({op} {threshold}).").format(value=value, op=row.operator, threshold=row.threshold)
    lead = f" Act within {int(row.lead_time_h)} h." if row.lead_time_h and not pd.isna(row.lead_time_h) else ""
    stage = ", ".join(STAGE_NAME.get(s, s) for s in str(row.stage).split("|"))
    ev = [{"tag": "General", "text": f"Trigger: {summ}"},
          {"tag": "General", "text": f"Crop stage: {stage} (calendar estimate)."},
          {"tag": "General", "text": f"Next days (replay of the real 2025 weather): {_forecast_line(frame, d, 3)}."},
          {"tag": "Your field", "text": f"{parcel['name']}: {parcel['variety']}, {parcel['ha']:g} ha, {parcel['irrigation']}"
                                         f"{', altitude ' + str(parcel['altitude_m']) + ' m' if parcel.get('altitude_m') else ''}."}]
    if row.note:
        ev.append({"tag": "General", "text": f"How it is measured: {row.note}."})
    return _alert(f"{parcel['id']}|{row.rule_id}", d, farmer, parcel, hazard, row.severity, title=title, summary=summ,
                  advice={"headline": (steps[0] if steps else "Review this plot.") + lead, "steps": steps[1:] or steps,
                          "confidence": CONF.get(str(row.confidence).lower(), "Confidence not rated"), "lead_time_h": _num(row.lead_time_h)},
                  evidence=ev, rule={"id": row.rule_id, "value": value, "operator": row.operator, "threshold": row.threshold,
                                     "unit": row.unit, "validated": bool(row.validated), "source_url": row.source_url},
                  source="Decision table (literature): " + (row.source_url or "no URL"), demo_data=False)


def _soil_drying(d, farmer, parcel, frame) -> dict | None:
    cfg = water_cfg()["soil_drying"]
    if parcel["irrigation"] != "drip irrigation" or d.month not in cfg["active_months"] or d not in frame.index:
        return None
    sm = frame[cfg["layer"]]
    low = float(sm.quantile(cfg["percentile"] / 100))
    cur = float(sm.loc[d])
    nx = _next_days(frame, d, cfg["lookahead_days"])
    rain_next = float(nx["precip_mm"].sum()) if len(nx) else 0.0
    if not (cur < low and rain_next < cfg["rain_free_mm"] + 20):
        return None
    wet = nx[nx["precip_mm"] >= 5]
    pev = float(nx["pev_mm"].mean()) if len(nx) else float(frame.loc[d, "pev_mm"])
    etc = ETC_KC * pev
    days = (wet.index[0] - d).days - 1 if len(wet) else cfg["lookahead_days"]
    apply_mm = max(8, round(etc * max(1, days)))
    hot = float(frame.loc[d, "tmax_c"]) >= cfg["hot_tmax_c"]
    sev = "high" if hot or not len(wet) else "moderate"
    skip = f", then skip {_weekday(wet.index[0])}" if len(wet) else ""
    steps = [f"Run your drip lines at 05:00 tomorrow to apply about {apply_mm} mm (about {apply_mm * 10} m³ per ha).",
             f"Skip {_weekday(wet.index[0])}: {float(wet['precip_mm'].iloc[0]):.0f} mm of rain is expected." if len(wet) else "No useful rain in the next 3 days, so keep the normal schedule after this run.",
             "Check the far end of the drip lines for low flow."]
    ev = [{"tag": "General", "text": f"Forecast (replay of the real next days): {_forecast_line(frame, d, 3)}."},
          {"tag": "General", "text": f"Water demand: about {etc:.1f} mm per day (reference evaporation × olive crop factor {ETC_KC})."},
          {"tag": "General", "text": f"Soil moisture 28–100 cm (ERA5-Land model): {cur * 100:.0f}%, below this plot's usual dry level of {low * 100:.0f}%."},
          {"tag": "Your field", "text": f"{parcel['name']}: {parcel['variety']}, {parcel['ha']:g} ha, drip irrigation."},
          {"tag": "Your field", "text": f"Irrigation log (demo data): last run {2 + _h(parcel['id'] + str(d.date())) % 5} days ago."}]
    return _alert(f"{parcel['id']}|SOIL-DRYING", d, farmer, parcel, "soil_drying", sev,
                  title=TITLE["soil_drying"].format(plot=parcel["name"]),
                  summary=f"Moisture at 28–100 cm is down to {cur * 100:.0f}%" + (" and no rain is expected before " + _weekday(wet.index[0]) + "." if len(wet) else " and no useful rain is expected."),
                  advice={"headline": f"Irrigate tomorrow at 05:00 to apply about {apply_mm} mm{skip}.", "steps": steps,
                          "confidence": CONF[cfg["confidence"]], "lead_time_h": 24.0}, evidence=ev,
                  rule={"id": "KAIROS-WATER-01", "value": round(cur * 100, 1), "operator": "<", "threshold": round(low * 100, 1), "unit": "% soil moisture",
                        "validated": False, "source_url": ""}, source=cfg["source"], demo_data=True)


def _rain_ahead(d, farmer, frame) -> dict | None:
    cfg = water_cfg()["rain_ahead"]
    irrigated = [p for p in farmer["parcels"] if p["irrigation"] == "drip irrigation"]
    if not irrigated:
        return None
    nx = _next_days(frame, d, cfg["lookahead_days"])
    if nx.empty or float(nx["precip_mm"].max()) < cfg["rain_mm"]:
        return None
    day = nx["precip_mm"].idxmax()
    mm = float(nx["precip_mm"].max())
    steps = [f"Cancel or shorten irrigation on {_weekday(day)}.", f"Expect about {mm:.0f} mm; restart when the topsoil dries out.",
             "Check drains and erosion on slopes after the rain."]
    return _alert(f"{farmer['id']}|RAIN-AHEAD", d, farmer, None, "rain_ahead", "moderate",
                  title=TITLE["rain_ahead"].format(day=_weekday(day), mm=f"{mm:.0f}"), subtitle="All parcels · adjust your irrigation plan",
                  summary=f"{mm:.0f} mm expected on {_weekday(day)}.",
                  advice={"headline": f"Skip irrigation on {_weekday(day)}.", "steps": steps, "confidence": CONF[cfg["confidence"]], "lead_time_h": 48.0},
                  evidence=[{"tag": "General", "text": f"Forecast (replay of the real next days): {_forecast_line(frame, d, 3)}."}],
                  rule={"id": "KAIROS-RAIN-01", "value": round(mm, 1), "operator": ">=", "threshold": cfg["rain_mm"], "unit": "mm/day",
                        "validated": False, "source_url": ""}, source=cfg["source"], demo_data=True)


def _water_use(d, farmer) -> dict | None:
    irrigated = [p for p in farmer["parcels"] if p["irrigation"] == "drip irrigation"]
    if not irrigated or d.weekday() != 3 or d.month not in (5, 6, 7, 8, 9, 10):
        return None
    pct = 80 + _h(farmer["id"] + str(d.date())) % 19
    p = irrigated[0]
    return _alert(f"{farmer['id']}|WATER-USE", d, farmer, p, "water_use", "info", title=TITLE["water_use"].format(pct=pct),
                  summary=f"{p['name']} has used {pct}% of this month's water plan (demo irrigation log).",
                  advice={"headline": "No action needed; keep to the plan.", "steps": ["Check the flow meter reading at the end of the week."],
                          "confidence": "Demo data", "lead_time_h": None},
                  evidence=[{"tag": "Your field", "text": "Irrigation log and plan are simulated for the demo."}],
                  rule={"id": "DEMO-WATER-USE", "value": pct, "operator": "<=", "threshold": 100, "unit": "% of plan", "validated": False, "source_url": ""},
                  source="Simulated irrigation log", demo_data=True)


def alerts_on(farmer_id: str, d: str, include_info: bool = False) -> list[dict]:
    ts = pd.Timestamp(d)
    farmer = farmer_index()[farmer_id]
    out: list[dict] = []
    for p in farmer["parcels"]:
        frame = cell_of(p)
        t = cell_table_alerts(p["cell"][0], p["cell"][1], reviews.mtime())
        if not t.empty:
            for row in t[t["date"] == ts].itertuples():
                if row.severity != "info" or include_info:
                    out.append(_table_alert(row, ts, farmer, p, frame))
        sd = _soil_drying(ts, farmer, p, frame)
        if sd:
            out.append(sd)
    ra = _rain_ahead(ts, farmer, cell_of(farmer["parcels"][0]))
    if ra:
        out.append(ra)
    wu = _water_use(ts, farmer)
    if wu:
        out.append(wu)
    ha = {p["id"]: p["ha"] for p in farmer["parcels"]}
    out.sort(key=lambda a: (-SEVERITY_RANK[a["severity"]], -ha.get(a["parcel_id"], 0), a["time"]))
    return out


def with_review(alert: dict, state: dict) -> dict:
    r = state["reviews"].get(alert["id"])
    return {**alert, "review": r, "done": alert["id"] in state["done"],
            "asked": any(q["alert_id"] == alert["id"] for q in state["requests"])}


def farmer_feed(farmer_id: str, d: str, kind: str | None = None) -> list[dict]:
    state = get_state()
    today = alerts_on(farmer_id, d)
    seen = {(a["parcel_id"], a["hazard"]) for a in today}
    yday = [a for a in alerts_on(farmer_id, str((pd.Timestamp(d) - timedelta(days=1)).date()))
            if a["severity"] in ("info", "moderate", "high", "severe") and (a["parcel_id"], a["hazard"]) not in seen]
    items = [{**with_review(a, state), "when": a["time"]} for a in today] + [{**with_review(a, state), "when": "Yesterday"} for a in yday
                                                                          if a["id"] not in {x["id"] for x in today}]
    # community warnings from verified field reports nearby (never the reporter's identity)
    f = farmer_index()[farmer_id]
    seen_comm: set = set()
    for rep in state["reports"]:
        key = (rep["label"], rep["municipality"])
        if key in seen_comm:
            continue
        if rep["status"] == "verified" and rep["visibility"] == "nearby" and rep["farmer_id"] != farmer_id and rep.get("warned_farmers") and farmer_id in rep["warned_farmers"]:
            seen_comm.add(key)
            items.append({"id": f"community|{rep['id']}", "date": d, "time": rep["verified_at_time"], "when": rep["verified_at_time"], "farmer_id": farmer_id,
                          "parcel_id": None, "parcel_name": None, "hazard": "community", "kind": "weather", "severity": "moderate", "severity_ui": "Medium",
                          "title": f"{rep['label']} reported near {rep['municipality']}", "subtitle": "Verified by your advisor · area warning",
                          "summary": f"Growers within {rep['radius_km']} km were warned. Check your own plots.", "community": True,
                          "advice": {"headline": f"Scout your plots for {rep['label'].lower()} this week.", "steps": ["Walk the north and south edges first.", "Tell your advisor what you find."],
                                     "confidence": "Advisor verified", "lead_time_h": None}, "evidence": [{"tag": "General", "text": "Report verified by an advisor. Reporter stays anonymous."}],
                          "rule": None, "source": "Field report", "demo_data": False, "review": {"status": "validated", "by": advisor()["name"]}, "done": False, "asked": False})
    if kind:
        items = [i for i in items if i["kind"] == kind]
    ha = {pid: p["ha"] for pid, (_, p) in parcel_index().items()}
    items.sort(key=lambda a: (a["when"] == "Yesterday", -SEVERITY_RANK[a["severity"]], -ha.get(a["parcel_id"], 0), a["time"]))
    return items[:10] if f else items


def find_alert(alert_id: str) -> dict | None:
    if alert_id.startswith("community|"):
        return None
    pid_or_fid = alert_id.split("|", 1)[0]
    d = alert_id.rsplit("|", 1)[-1]
    fid = pid_or_fid if pid_or_fid.startswith("F") and "-" not in pid_or_fid else parcel_index()[pid_or_fid][0]["id"]
    for a in alerts_on(fid, d, include_info=True):
        if a["id"] == alert_id:
            return a
    return None


# ---------- shared state ----------
def _seed() -> dict:
    state = {"clock": DEFAULT_CLOCK, "requests": [], "reports": [], "reviews": {}, "done": [], "chat": {}, "seq": 0}
    return state


_state: dict | None = None


def get_state() -> dict:
    global _state
    with LOCK:
        if _state is None:
            if STATE_FILE.exists():
                _state = json.loads(STATE_FILE.read_text())
            else:
                _state = _seed()
                seed_demo(_state)
                save()
        return _state


def save() -> None:
    with LOCK:
        STATE_FILE.write_text(json.dumps(_state, ensure_ascii=False))


def reset() -> dict:
    global _state
    with LOCK:
        _state = _seed()
        seed_demo(_state)
        save()
        return _state


def _now() -> str:
    return datetime.now(UTC).strftime("%H:%M")


def next_id(state: dict, prefix: str) -> str:
    state["seq"] += 1
    return f"{prefix}{state['seq']:03d}"


def seed_demo(state: dict) -> None:
    """Pre-load a lived-in demo: one open request, one reviewed alert, two field reports."""
    d = state["clock"]
    ja = [a for a in alerts_on("F01", d, include_info=True) if a["kind"] == "irrigation" or a["severity"] in ("high", "moderate")]
    if ja:
        a = ja[0]
        state["requests"].append({"id": next_id(state, "R"), "farmer_id": "F01", "alert_id": a["id"], "parcel_id": a["parcel_id"], "title": a["title"],
                                  "subtitle": a["subtitle"], "message": "Leaves on the south side look curled. Photos are from 3 trees. Should I irrigate longer than 6 hours?",
                                  "urgency": "Today", "share_data": True, "photos": [{"label": "Leaves, south side", "thumb": None}, {"label": "Drip emitter", "thumb": None}],
                                  "status": "asked", "created_at": "18:42", "ts": time.time() - 3000, "clock_date": d, "replies": []})
    carmen = farmer_index().get("F03")
    if carmen:
        ca = alerts_on("F03", d, include_info=True)
        if ca:
            a = ca[0]
            state["requests"].append({"id": next_id(state, "R"), "farmer_id": "F03", "alert_id": a["id"], "parcel_id": a["parcel_id"], "title": a["title"],
                                      "subtitle": a["subtitle"], "message": "Is this still the right moment to act before the harvest crew arrives?", "urgency": "This week",
                                      "share_data": True, "photos": [{"label": "Row view", "thumb": None}], "status": "asked", "created_at": "17:05", "ts": time.time() - 6000, "clock_date": d, "replies": []})
    j = farmer_index()["F01"]["parcels"][0]["centroid"]
    near = sorted((f for f in farmers() if f["id"] != "F01"), key=lambda f: min(km(j, p["centroid"]) for p in f["parcels"]))
    for f in [farmer_index()["F01"], near[0]]:
        p = f["parcels"][0]
        state["reports"].append({"id": next_id(state, "T"), "farmer_id": f["id"], "kind": "Pest", "label": "Olive fruit fly", "parcel_id": p["id"],
                                 "notes": "Small holes in olives on the north edge, about 1 in 5 on three trees.", "photos": [{"label": "Olives", "thumb": None}, {"label": "Tree", "thumb": None}],
                                 "visibility": "nearby", "status": "new", "municipality": f["municipality"], "centroid": p["centroid"], "created_at": "16:20", "ts": time.time() - 9000, "clock_date": d})
    juan_w = [a for a in alerts_on("F01", d, include_info=True) if a["hazard"] == "water_use"]
    if juan_w:
        state["reviews"][juan_w[0]["id"]] = {"status": "validated", "by": advisor()["name"], "note": "Looks right.", "at": "Yesterday"}


# ---------- actions ----------
def create_request(body: dict) -> dict:
    state = get_state()
    with LOCK:
        a = find_alert(body["alert_id"]) if body.get("alert_id") else None
        req = {"id": next_id(state, "R"), "farmer_id": body["farmer_id"], "alert_id": body.get("alert_id"), "parcel_id": body.get("parcel_id") or (a or {}).get("parcel_id"),
               "title": (a or {}).get("title", body.get("title", "Question")), "subtitle": (a or {}).get("subtitle", ""), "message": body.get("message", ""),
               "urgency": body.get("urgency", "Today"), "share_data": bool(body.get("share_data", True)), "photos": body.get("photos", [])[:6],
               "status": "asked", "created_at": _now(), "ts": time.time(), "clock_date": state["clock"], "replies": []}
        state["requests"].insert(0, req)
        save()
        return req


def respond_request(rid: str, body: dict) -> dict | None:
    state = get_state()
    with LOCK:
        req = next((r for r in state["requests"] if r["id"] == rid), None)
        if not req:
            return None
        decision = body.get("decision")  # validated | edited | rejected | reply
        text = body.get("text", "").strip()
        if decision in ("validated", "edited", "rejected") and req.get("alert_id"):
            state["reviews"][req["alert_id"]] = {"status": decision, "by": advisor()["name"], "note": text, "steps": body.get("steps"),
                                                 "headline": body.get("headline"), "at": _now()}
        if text or decision:
            default = {"validated": "I checked this advice and it stands.", "edited": "I adjusted the advice. See the updated steps.", "rejected": "Please do not follow this advice yet."}
            reply = {"from": "advisor", "text": text or default.get(decision, ""), "at": _now(), "decision": decision}
            req["replies"].append(reply)
            state["chat"].setdefault(req["farmer_id"], []).append({"from": "advisor", "text": reply["text"], "at": reply["at"], "ts": time.time(), "request_id": rid})
        req["status"] = "replied"
        save()
        return req


def review_alert(alert_id: str, body: dict) -> dict:
    state = get_state()
    with LOCK:
        state["reviews"][alert_id] = {"status": body["status"], "by": body.get("by", advisor()["name"]), "note": body.get("note", ""),
                                      "steps": body.get("steps"), "headline": body.get("headline"), "at": _now()}
        save()
        return state["reviews"][alert_id]


def create_report(body: dict) -> dict:
    state = get_state()
    f = farmer_index()[body["farmer_id"]]
    p = parcel_index().get(body.get("parcel_id") or "", (f, f["parcels"][0]))[1]
    kind = body.get("kind", "Pest")
    label = {"Pest": body.get("label") or "Pest sighting", "Disease": body.get("label") or "Disease sighting",
             "Irrigation fault": "Irrigation fault", "Weather damage": "Weather damage"}.get(kind, kind)
    with LOCK:
        rep = {"id": next_id(state, "T"), "farmer_id": f["id"], "kind": kind, "label": label, "parcel_id": p["id"], "notes": body.get("notes", ""),
               "photos": body.get("photos", [])[:6], "visibility": body.get("visibility", "advisor"), "status": "new", "municipality": f["municipality"],
               "centroid": p["centroid"], "created_at": _now(), "ts": time.time(), "clock_date": state["clock"]}
        state["reports"].insert(0, rep)
        save()
        return rep


def verify_report(rid: str, body: dict) -> dict | None:
    state = get_state()
    with LOCK:
        rep = next((r for r in state["reports"] if r["id"] == rid), None)
        if not rep:
            return None
        action = body.get("action", "verify")
        if action == "dismiss":
            rep["status"] = "dismissed"
        else:
            rep["status"] = "verified"
            rep["radius_km"] = 10
            rep["verified_at_time"] = _now()
            near = [f["id"] for f in farmers() if f["id"] != rep["farmer_id"] and any(km(rep["centroid"], p["centroid"]) <= 10 for p in f["parcels"])]
            rep["warned_farmers"] = near if rep["visibility"] == "nearby" else []
            same = [r for r in state["reports"] if r["id"] != rid and r["label"] == rep["label"] and r["status"] == "new" and km(r["centroid"], rep["centroid"]) <= 10]
            for r in same:
                r["status"] = "verified"
                r["radius_km"], r["verified_at_time"], r["warned_farmers"] = 10, rep["verified_at_time"], rep["warned_farmers"]
        save()
        return rep


def set_clock(d: str) -> str:
    state = get_state()
    with LOCK:
        state["clock"] = d
        save()
    return d


def send_chat(farmer_id: str, who: str, text: str) -> dict:
    state = get_state()
    with LOCK:
        msg = {"from": who, "text": text, "at": _now(), "ts": time.time()}
        state["chat"].setdefault(farmer_id, []).append(msg)
        save()
        return msg


# ---------- views ----------
def farmer_view(farmer_id: str) -> dict:
    f = farmer_index()[farmer_id]
    return {k: v for k, v in f.items() if k != "parcels"} | {"parcels": [{k: v for k, v in p.items() if k != "polygon"} for p in f["parcels"]],
                                                              "parcel_count": len(f["parcels"])}


def advisor_overview(d: str) -> dict:
    state = get_state()
    rows, water_farmers, review_farmers = [], set(), set()
    open_reqs = [r for r in state["requests"] if r["status"] == "asked"]
    for f in farmers():
        al = [with_review(a, state) for a in alerts_on(f["id"], d)]
        al = [a for a in al if a["severity"] != "info"]
        unrev = [a for a in al if not a["review"]]
        water = [a for a in unrev if a["kind"] == "irrigation" and a["severity"] in ("moderate", "high", "severe")]
        high = [a for a in unrev if a["severity"] in ("high", "severe")]
        fr = [r for r in open_reqs if r["farmer_id"] == f["id"]]
        if water:
            water_farmers.add(f["id"])
        if fr or high:
            review_farmers.add(f["id"])
        top = max(unrev, key=lambda a: SEVERITY_RANK[a["severity"]], default=None)
        rows.append({"farmer": {k: f[k] for k in ("id", "name", "initials", "farm", "place", "municipality", "ha")} | {"parcel_count": len(f["parcels"])},
                     "open_requests": fr, "top_alert": top, "alert_count": len(unrev), "water": bool(water), "needs_review": bool(fr or high),
                     "high_count": len(high)})
    reports = [r for r in state["reports"] if r["status"] == "new"]
    clusters: dict[tuple, dict] = {}
    for r in reports:
        key = (r["label"], r["municipality"])
        c = clusters.setdefault(key, {"label": r["label"], "municipality": r["municipality"], "kind": r["kind"], "reports": [], "centroid": r["centroid"]})
        c["reports"].append(r)
    for c in clusters.values():
        c["farms_within_10km"] = sum(1 for f in farmers() if any(km(c["centroid"], p["centroid"]) <= 10 for p in f["parcels"]))
        c["growers"] = [farmer_index()[r["farmer_id"]]["name"] for r in c["reports"]]
    return {"advisor": advisor(), "date": d, "farmer_count": len(rows), "to_review": len(review_farmers | {r["farmer_id"] for r in open_reqs}),
            "water_alerts": len(water_farmers), "new_reports": len(reports), "rows": rows, "report_clusters": list(clusters.values())}


def dashboard(d: str) -> dict:
    state = get_state()
    parcels = []
    for f in farmers():
        by_parcel: dict[str, list] = {}
        for a in alerts_on(f["id"], d, include_info=True):
            by_parcel.setdefault(a["parcel_id"] or f["parcels"][0]["id"], []).append(with_review(a, state))
        for p in f["parcels"]:
            al = sorted(by_parcel.get(p["id"], []), key=lambda a: -SEVERITY_RANK[a["severity"]])
            parcels.append({"id": p["id"], "farmer_id": f["id"], "farmer": f["name"], "farm": f["farm"], "name": p["name"], "ha": p["ha"], "variety": p["variety"],
                            "irrigation": p["irrigation"], "polygon": p["polygon"], "centroid": p["centroid"], "sigpac_ref": p["sigpac_ref"],
                            "municipality": f["municipality"], "province": f["province"], "slope_pct": p["slope_pct"], "altitude_m": p["altitude_m"],
                            "attrs_source": p["attrs_source"], "top_severity": al[0]["severity"] if al else None, "alerts": al})
    counts = {"parcels": len(parcels), "with_alerts": sum(1 for p in parcels if any(a["severity"] != "info" for a in p["alerts"])),
              "pending": sum(1 for p in parcels for a in p["alerts"] if a["severity"] != "info" and not a["review"]),
              "validated": sum(1 for p in parcels for a in p["alerts"] if a["review"] and a["review"]["status"] == "validated"),
              "edited": sum(1 for p in parcels for a in p["alerts"] if a["review"] and a["review"]["status"] == "edited"),
              "rejected": sum(1 for p in parcels for a in p["alerts"] if a["review"] and a["review"]["status"] == "rejected")}
    return {"date": d, "counts": counts, "parcels": parcels, "advisor": advisor(), "rules": {"evaluable": len(load_ruleset().rules), "not_evaluable": len(load_ruleset().not_evaluable)}}


WX_COLS = ["tmax_c", "tmin_c", "tmean_c", "precip_mm", "precip_max_12h_mm", "rh_mean_pct", "rh_min_pct", "wet_hours_8_24c", "soil_moisture_l1",
           "soil_moisture_l2", "soil_moisture_l3", "soil_temp_l1_c", "pev_mm", "gust_max_ms", "gdd_base9_1"]


def parcel_weather(pid: str, d: str, days: int = 30, ahead: int = 4) -> dict:
    """Daily ERA5-Land series for the cell a plot sits in: `days` back from d, `ahead` days of replay look-ahead."""
    _, p = parcel_index()[pid]
    frame = cell_of(p)
    ts = pd.Timestamp(d)
    w = frame.loc[ts - timedelta(days=days - 1): ts + timedelta(days=ahead)]
    return {"parcel_id": pid, "date": d, "today_index": int((w.index <= ts).sum()) - 1, "dates": [str(i.date()) for i in w.index],
            **{c: [None if pd.isna(v) else round(float(v), 3) for v in w[c]] for c in WX_COLS if c in w}, "cell": p["cell"],
            "dry_level": round(float(frame["soil_moisture_l3"].quantile(water_cfg()["soil_drying"]["percentile"] / 100)), 3)}


def stages(d: str) -> list[str]:
    return [STAGE_NAME.get(s, s) for s in active_stages(date.fromisoformat(d))]
