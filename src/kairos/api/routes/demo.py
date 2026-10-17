"""Shared demo endpoints for the farmer app, advisor app and advisor dashboard."""
from fastapi import APIRouter, HTTPException

from kairos.demo import core

router = APIRouter()


def _date(d: str | None) -> str:
    d = d or core.get_state()["clock"]
    lo, hi = core.date_range()
    if not (lo <= d <= hi):
        raise HTTPException(422, f"date must be between {lo} and {hi}")
    return d


@router.get("/meta")
def meta() -> dict:
    lo, hi = core.date_range()
    return {"advisor": core.advisor(), "clock": core.get_state()["clock"], "date_min": lo, "date_max": hi, "mode": "replay",
            "notice": "Real 2025 ERA5 weather replayed as if live. Names, varieties and the irrigation log are demo data."}


@router.get("/clock")
def clock() -> dict:
    return {"clock": core.get_state()["clock"]}


@router.post("/clock")
def set_clock(body: dict) -> dict:
    return {"clock": core.set_clock(_date(body.get("date")))}


@router.post("/reset")
def reset() -> dict:
    core.reset()
    return {"ok": True, "clock": core.get_state()["clock"]}


@router.get("/farmers")
def farmers() -> list[dict]:
    return [core.farmer_view(f["id"]) for f in core.farmers()]


@router.get("/farmers/{fid}")
def farmer(fid: str, date: str | None = None) -> dict:
    if fid not in core.farmer_index():
        raise HTTPException(404, "unknown farmer")
    d = _date(date)
    out = core.farmer_view(fid)
    out["stages"] = core.stages(d)
    return out


@router.get("/farmers/{fid}/alerts")
def feed(fid: str, date: str | None = None, kind: str | None = None) -> list[dict]:
    if fid not in core.farmer_index():
        raise HTTPException(404, "unknown farmer")
    return core.farmer_feed(fid, _date(date), kind)


@router.get("/farmers/{fid}/parcels")
def parcels(fid: str, date: str | None = None) -> list[dict]:
    if fid not in core.farmer_index():
        raise HTTPException(404, "unknown farmer")
    d = _date(date)
    al = core.alerts_on(fid, d)
    out = []
    for p in core.farmer_index()[fid]["parcels"]:
        mine = [a for a in al if a["parcel_id"] == p["id"]]
        out.append({**p, "alerts": len(mine), "top_severity": max((a["severity"] for a in mine), key=lambda s: core.SEVERITY_RANK[s], default=None)})
    return out


@router.get("/alerts/{alert_id:path}")
def alert(alert_id: str) -> dict:
    a = core.find_alert(alert_id)
    if not a:
        raise HTTPException(404, "alert not found for that plot and date")
    return core.with_review(a, core.get_state())


@router.post("/alerts/{alert_id:path}/done")
def done(alert_id: str) -> dict:
    s = core.get_state()
    with core.LOCK:
        if alert_id not in s["done"]:
            s["done"].append(alert_id)
        core.save()
    return {"ok": True}


@router.post("/review/{alert_id:path}")
def review(alert_id: str, body: dict) -> dict:
    if body.get("status") not in ("validated", "edited", "rejected"):
        raise HTTPException(422, "status must be validated, edited or rejected")
    return core.review_alert(alert_id, body)


@router.get("/requests")
def requests(farmer_id: str | None = None, status: str | None = None) -> list[dict]:
    rs = core.get_state()["requests"]
    return [r for r in rs if (not farmer_id or r["farmer_id"] == farmer_id) and (not status or r["status"] == status)]


@router.post("/requests")
def create_request(body: dict) -> dict:
    if body.get("farmer_id") not in core.farmer_index():
        raise HTTPException(404, "unknown farmer")
    return core.create_request(body)


@router.post("/requests/{rid}/respond")
def respond(rid: str, body: dict) -> dict:
    out = core.respond_request(rid, body)
    if out is None:
        raise HTTPException(404, "request not found")
    return out


@router.get("/reports")
def reports(status: str | None = None, farmer_id: str | None = None) -> list[dict]:
    rs = core.get_state()["reports"]
    return [r for r in rs if (not status or r["status"] == status) and (not farmer_id or r["farmer_id"] == farmer_id)]


@router.post("/reports")
def create_report(body: dict) -> dict:
    if body.get("farmer_id") not in core.farmer_index():
        raise HTTPException(404, "unknown farmer")
    return core.create_report(body)


@router.post("/reports/{rid}/verify")
def verify(rid: str, body: dict | None = None) -> dict:
    out = core.verify_report(rid, body or {})
    if out is None:
        raise HTTPException(404, "report not found")
    return out


@router.get("/chat/{fid}")
def chat(fid: str) -> list[dict]:
    return core.get_state()["chat"].get(fid, [])


@router.post("/chat/{fid}")
def send_chat(fid: str, body: dict) -> dict:
    return core.send_chat(fid, body.get("from", "farmer"), body.get("text", ""))


@router.get("/advisor/overview")
def advisor_overview(date: str | None = None) -> dict:
    return core.advisor_overview(_date(date))


@router.get("/dashboard")
def dashboard(date: str | None = None) -> dict:
    return core.dashboard(_date(date))


@router.get("/parcels/{pid}/weather")
def parcel_weather(pid: str, date: str | None = None, days: int = 30) -> dict:
    if pid not in core.parcel_index():
        raise HTTPException(404, "unknown plot")
    return core.parcel_weather(pid, _date(date), min(max(days, 7), 400))


@router.post("/assist/ask")
def assist_ask(body: dict) -> dict:
    from kairos.assist import ask

    alert = core.find_alert(body["alert_id"]) if body.get("alert_id") else None
    return ask.answer(body.get("question", ""), alert)


@router.post("/assist/feedback")
def assist_feedback(body: dict) -> dict:
    from kairos.assist import feedback

    feedback.rate(body["answer_id"], body["verdict"], body.get("advisor", core.advisor()["name"]), body.get("corrected", ""), body.get("note", ""))
    return {"ok": True}


@router.get("/assist/feedback")
def assist_feedback_list() -> list[dict]:
    from kairos.assist import feedback

    return feedback.records()[-100:]


@router.post("/assist/explain")
def assist_explain(body: dict) -> dict:
    from kairos.assist import ask

    alert = core.find_alert(body["alert_id"])
    if not alert:
        raise HTTPException(404, "alert not found")
    return ask.explain(alert)


@router.get("/basemap/satellite.json")
def satellite_style() -> dict:
    """MapLibre style with Esri World Imagery, so the Streamlit map can show satellite tiles (a deck.gl TileLayer cannot draw raster tiles from pydeck)."""
    url = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    return {"version": 8, "sources": {"sat": {"type": "raster", "tiles": [url], "tileSize": 256, "maxzoom": 19, "attribution": "Esri, Maxar, Earthstar Geographics"}},
            "layers": [{"id": "sat", "type": "raster", "source": "sat"}]}
