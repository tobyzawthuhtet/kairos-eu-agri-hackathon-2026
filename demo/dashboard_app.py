"""Kairos advisor dashboard (Streamlit).

Talks to the same demo API as the farmer and advisor apps (KAIROS_API, default http://localhost:8000), so a request sent
in the farmer app or a validation made here shows up everywhere. Run it with `make demo-up`.
"""
import base64
import os
from datetime import date

import altair as alt
import httpx
import pandas as pd
import pydeck as pdk
import streamlit as st

API = os.environ.get("KAIROS_API", "http://localhost:8000").rstrip("/") + "/demo"
RGB = {"severe": (154, 58, 42), "high": (154, 58, 42), "moderate": (224, 180, 58), "low": (217, 207, 122), "info": (169, 185, 124), "none": (127, 154, 82)}
LABEL = {"severe": "High", "high": "High", "moderate": "Medium", "low": "Low", "info": "Info"}
RANK = {"info": 0, "low": 1, "moderate": 2, "high": 3, "severe": 4}
BADGE = {"High": "red", "Medium": "orange", "Low": "yellow", "Info": "green"}

st.set_page_config(page_title="Kairos Advisor Dashboard", page_icon="🫒", layout="wide")
st.markdown("""<style>
.block-container{padding-top:1.4rem;max-width:1700px}
div[data-testid="stMetricValue"] div{white-space:normal;overflow:visible;text-overflow:clip;font-size:1.4rem}
div[data-testid="stMetric"]{background:#fff;border:1px solid #e7e5d8;border-radius:16px;padding:10px 16px}
.stApp{background:#f5f4ec}
</style>""", unsafe_allow_html=True)


def api_get(path: str, **params):
    r = httpx.get(API + path, params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def api_post(path: str, body: dict | None = None):
    r = httpx.post(API + path, json=body or {}, timeout=60)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=120, show_spinner=False)
def weather(pid: str, clock: str) -> pd.DataFrame:
    w = api_get(f"/parcels/{pid}/weather", date=clock, days=400)
    df = pd.DataFrame({k: v for k, v in w.items() if isinstance(v, list) and len(v) == len(w["dates"]) and k != "dates"})
    df.insert(0, "date", pd.to_datetime(w["dates"]))
    df.attrs["dry_level"] = w["dry_level"]
    return df


def thumb_bytes(data_url: str | None):
    return base64.b64decode(data_url.split(",", 1)[1]) if data_url and "," in data_url else None


# ---------------- data ----------------
try:
    meta = api_get("/meta")
except Exception as e:  # noqa: BLE001
    st.error(f"Cannot reach the Kairos API at {API} ({e}). Start everything with `make demo-up`.")
    st.stop()
clock = meta["clock"]
data = api_get("/dashboard", date=clock)
reqs = api_get("/requests")
reps = api_get("/reports")
plots = data["parcels"]
by_id = {p["id"]: p for p in plots}
open_reqs = [r for r in reqs if r["status"] == "asked"]
new_reps = [r for r in reps if r["status"] == "new"]

# ---------------- sidebar ----------------
with st.sidebar:
    st.markdown("### 🫒 Kairos")
    st.caption(f"Advisor dashboard · {data['advisor']['name']} · {data['advisor']['area']}")
    picked = st.date_input("Replay date (real 2025 weather)", value=date.fromisoformat(clock), min_value=date.fromisoformat(meta["date_min"]),
                           max_value=date.fromisoformat(meta["date_max"]))
    if str(picked) != clock:
        api_post("/clock", {"date": str(picked)})
        st.rerun()
    st.divider()
    st.markdown("**Filters**")
    q = st.text_input("Search plot, grower or municipality")
    sev_f = st.multiselect("Severity", ["High", "Medium", "Low"], default=[])
    status_f = st.selectbox("Review status", ["Any", "Pending", "Validated", "Edited", "Held off"])
    kind_f = st.radio("Alert type", ["All", "Weather", "Irrigation"], horizontal=True)
    only_alerts = st.toggle("Only plots with alerts", value=False)
    st.divider()
    auto = st.toggle("Auto-refresh every 6 s", value=True, help="Picks up new grower requests and reports.")
    c1, c2 = st.columns(2)
    if c1.button("Refresh", width="stretch"):
        st.cache_data.clear()
        st.rerun()
    if c2.button("Reset demo", width="stretch"):
        api_post("/reset")
        st.cache_data.clear()
        st.session_state.pop("sel", None)
        st.rerun()
    st.caption("Replay of reanalysis, not a forecast. Thresholds are literature-based and pending agronomist validation.")


def visible(p: dict) -> bool:
    al = [a for a in p["alerts"] if a["severity"] != "info"]
    if q and q.lower() not in f"{p['name']} {p['farmer']} {p['farm']} {p['municipality']}".lower():
        return False
    if only_alerts and not al:
        return False
    if sev_f and not any(LABEL[a["severity"]] in sev_f for a in al):
        return False
    if kind_f != "All" and not any(a["kind"] == kind_f.lower() for a in al):
        return False
    if status_f == "Pending" and not any(not a["review"] for a in al):
        return False
    key = {"Validated": "validated", "Edited": "edited", "Held off": "rejected"}.get(status_f)
    return not (key and not any(a["review"] and a["review"]["status"] == key for a in al))


vis = [p for p in plots if visible(p)]
vis_ids = {p["id"] for p in vis}

# ---------------- header + KPIs ----------------
st.title("Advisor dashboard")
st.caption(f"{date.fromisoformat(clock):%A %d %B %Y} · replay of real ERA5-Land weather on real LPIS olive plots")
c = data["counts"]
for col, (label, val) in zip(st.columns(8), [("Plots (LPIS)", c["parcels"]), ("Plots with alerts", c["with_alerts"]), ("Pending review", c["pending"]),
                                              ("Validated", c["validated"]), ("Edited", c["edited"]), ("Held off", c["rejected"]),
                                              ("Open grower requests", len(open_reqs)), ("New field reports", len(new_reps))], strict=True):
    col.metric(label, val)


# ---------------- actions ----------------
def review(alert_id: str, status: str, note: str = "", headline: str | None = None, steps: list[str] | None = None):
    api_post("/review/" + alert_id.replace("/", "%2F"), {"status": status, "note": note, "headline": headline, "steps": steps})
    st.toast({"validated": "Validated. The grower sees “Checked by advisor”.", "edited": "Edited and validated.", "rejected": "Held off. The grower is told not to act yet."}[status])
    st.rerun()


def alert_card(a: dict, key: str, request_id: str | None = None):
    r = a["review"]
    with st.container(border=True):
        top = st.columns([3, 1])
        top[0].markdown(f":{BADGE[a['severity_ui']]}-badge[{a['severity_ui']}]  **{a['title']}**")
        status = "Pending" if not r else {"validated": "Validated", "edited": "Edited", "rejected": "Held off"}[r["status"]]
        top[1].markdown(f":{'orange' if not r else 'green' if r['status'] != 'rejected' else 'red'}-badge[{status}]")
        st.caption(a["summary"])
        steps = r["steps"] if r and r.get("steps") else a["advice"]["steps"]
        head = r["headline"] if r and r.get("headline") else a["advice"]["headline"]
        st.markdown(f"**Action the engine proposes:** {head}")
        for i, s in enumerate(steps, 1):
            st.markdown(f"{i}. {s}")
        meta_bits = [a["advice"]["confidence"], a["rule"]["id"] if a["rule"] else None,
                     "threshold not validated" if a["rule"] and not a["rule"]["validated"] else None, "demo rule / data" if a["demo_data"] else None,
                     f"act within {int(a['advice']['lead_time_h'])} h" if a["advice"].get("lead_time_h") else None]
        st.caption(" · ".join(b for b in meta_bits if b))
        with st.expander("Evidence and source"):
            for e in a["evidence"]:
                st.markdown(f"`{e['tag']}` {e['text']}")
            st.caption(a["source"])
            if a["rule"]:
                st.caption(f"Reading {a['rule']['value']} {a['rule']['operator']} {a['rule']['threshold']} {a['rule']['unit'] or ''}")
        if not a.get("community"):
            ek = f"exp-{key}"
            if st.button("Explain why the system triggered this (AI)", key=f"xb-{key}"):
                with st.spinner("Reading the rule and the evidence…"):
                    st.session_state[ek] = api_post("/assist/explain", {"alert_id": a["id"]})
            ex = st.session_state.get(ek)
            if ex:
                st.markdown(f":violet-badge[{'AI-drafted from the rules' if ex['backend'] == 'ollama' else 'Plain summary'}]")
                st.markdown(ex["text"])
                st.caption(" · ".join(ex["facts"]))
                st.caption("Sources: " + ", ".join(f"[{c['rule_id']}]({c['source_url']})" if c["source_url"] else c["rule_id"] for c in ex["citations"])
                           + (f" · {ex['note']}" if ex.get("note") else "") + " · Rate it in the AI answers tab.")
        if r:
            st.caption(f"{r['by']} · {r['at']}" + (f" · “{r['note']}”" if r.get("note") else ""))
        if a.get("community"):
            return
        note = st.text_input("Note for the grower (optional)", key=f"note-{key}")
        b = st.columns(3)
        if request_id:
            def answer(decision: str, headline=None, steps_=None):
                api_post(f"/requests/{request_id}/respond", {"decision": decision, "text": note, "headline": headline, "steps": steps_})
                st.toast("Answer sent to the grower.")
                st.rerun()
            if b[0].button("Validate and answer", key=f"va-{key}", type="primary"):
                answer("validated")
            if b[2].button("Hold off and answer", key=f"ho-{key}"):
                answer("rejected")
        else:
            if b[0].button("Validate", key=f"v-{key}", type="primary"):
                review(a["id"], "validated", note)
            if b[2].button("Hold off", key=f"h-{key}"):
                review(a["id"], "rejected", note)
        with b[1].popover("Edit advice"):
            nh = st.text_input("Headline", value=head, key=f"eh-{key}")
            ns = st.text_area("Steps (one per line)", value="\n".join(steps), key=f"es-{key}", height=140)
            if st.button("Save edit and " + ("answer" if request_id else "validate"), key=f"se-{key}"):
                lines = [s.strip() for s in ns.splitlines() if s.strip()]
                if request_id:
                    api_post(f"/requests/{request_id}/respond", {"decision": "edited", "text": note, "headline": nh, "steps": lines})
                    st.toast("Edited advice sent to the grower.")
                    st.rerun()
                else:
                    review(a["id"], "edited", note, nh, lines)


# ---------------- weather time series ----------------
def weather_panel(p: dict):
    df = weather(p["id"], clock)
    today = pd.Timestamp(clock)
    st.markdown("##### Weather time series at this plot")
    st.caption(f"ERA5-Land daily values for the 0.1° cell containing the plot (about 9 km). The last 4 days are the replay look-ahead. "
               f"Dashed line = today ({clock}).")
    lo, hi = df["date"].min().date(), df["date"].max().date()
    default_lo = max(lo, (today - pd.Timedelta(days=90)).date())
    rng = st.slider("Date range", min_value=lo, max_value=hi, value=(default_lo, hi), key=f"rng-{p['id']}")
    d = df[(df["date"].dt.date >= rng[0]) & (df["date"].dt.date <= rng[1])]
    rule = alt.Chart(pd.DataFrame({"date": [today]})).mark_rule(color="black", strokeDash=[4, 3]).encode(x="date:T")
    base = alt.Chart(d).encode(x=alt.X("date:T", title=None))

    def lines(cols: dict[str, str], title: str, extra=None):
        long = d.melt("date", list(cols), var_name="v", value_name="val").assign(series=lambda x: x["v"].map(cols))
        ch = alt.Chart(long).mark_line().encode(x=alt.X("date:T", title=None), y=alt.Y("val:Q", title=title, scale=alt.Scale(zero=False)),
                                                 color=alt.Color("series:N", legend=alt.Legend(orient="bottom", title=None)), tooltip=["date:T", "series:N", alt.Tooltip("val:Q", format=".2f")])
        return (ch + rule + (extra if extra is not None else rule)).properties(height=250).interactive(bind_y=False)

    t1, t2, t3, t4, t5 = st.tabs(["Temperature & rain", "Soil moisture", "Humidity & leaf wetness", "Wind & evaporation", "Growth (degree-days)"])
    with t1:
        rain = base.mark_bar(color="#6c8fc4", opacity=.8).encode(y=alt.Y("precip_mm:Q", title="Rain (mm/day)"), tooltip=["date:T", alt.Tooltip("precip_mm:Q", format=".1f")]).properties(height=110)
        st.altair_chart(lines({"tmax_c": "Daily max", "tmean_c": "Daily mean", "tmin_c": "Daily min"}, "Temperature (°C)"), width="stretch")
        st.altair_chart(rain + rule, width="stretch")
    with t2:
        dry = alt.Chart(pd.DataFrame({"y": [df.attrs["dry_level"]]})).mark_rule(color="#9a3a2a", strokeDash=[5, 3]).encode(y="y:Q")
        st.altair_chart(lines({"soil_moisture_l1": "0–7 cm", "soil_moisture_l2": "7–28 cm", "soil_moisture_l3": "28–100 cm"}, "Soil moisture (m³/m³)", dry), width="stretch")
        st.caption(f"Red dashed line = this cell's 'dry' level for 28–100 cm (20th percentile of 2025): {df.attrs['dry_level']:.3f}. Used by the Kairos soil-drying rule.")
    with t3:
        st.altair_chart(lines({"rh_mean_pct": "Mean humidity (%)", "rh_min_pct": "Minimum humidity (%)"}, "Relative humidity (%)"), width="stretch")
        wet = base.mark_area(color="#46662f", opacity=.7).encode(y=alt.Y("wet_hours_8_24c:Q", title="Wet hours at 8–24 °C"), tooltip=["date:T", "wet_hours_8_24c:Q"]).properties(height=130)
        st.altair_chart(wet + rule, width="stretch")
        st.caption("Leaf wetness is a proxy: hours with humidity ≥ 90 % or rain, at 8–24 °C (peacock-spot infection weather).")
    with t4:
        g = d.assign(gust_kmh=d["gust_max_ms"] * 3.6)
        st.altair_chart((alt.Chart(g).mark_line(color="#3c4a78").encode(x=alt.X("date:T", title=None), y=alt.Y("gust_kmh:Q", title="Max gust (km/h)"), tooltip=["date:T", alt.Tooltip("gust_kmh:Q", format=".0f")]) + rule).properties(height=170), width="stretch")
        st.altair_chart((alt.Chart(d).mark_line(color="#e07b00").encode(x=alt.X("date:T", title=None), y=alt.Y("pev_mm:Q", title="Potential evaporation (mm/day)"), tooltip=["date:T", alt.Tooltip("pev_mm:Q", format=".1f")]) + rule).properties(height=170), width="stretch")
        st.caption("Gusts come from the coarser 0.25° ERA5 grid. ERA5-Land tends to overestimate potential evaporation.")
    with t5:
        full = df.assign(gdd_cum=df["gdd_base9_1"].cumsum())
        d2 = full[(full["date"].dt.date >= rng[0]) & (full["date"].dt.date <= rng[1])]
        st.altair_chart((alt.Chart(d2).mark_line(color="#2f4a1f").encode(x=alt.X("date:T", title=None), y=alt.Y("gdd_cum:Q", title="Degree-days since 1 Jan (base 9.1 °C)"), tooltip=["date:T", alt.Tooltip("gdd_cum:Q", format=".0f")])
                         + alt.Chart(pd.DataFrame({"y": [495]})).mark_rule(color="#9a3a2a", strokeDash=[5, 3]).encode(y="y:Q") + rule).properties(height=220), width="stretch")
        st.caption("Red line = 495 degree-days, the table's full-flowering estimate. Assumes dormancy release on 1 January.")
    with st.expander("Data table and download"):
        st.dataframe(d, width="stretch", hide_index=True)
        st.download_button("Download CSV", d.to_csv(index=False).encode(), file_name=f"{p['id']}_weather_{clock}.csv", mime="text/csv")


# ---------------- map ----------------
def build_map(sel_id: str | None):
    rows = []
    for p in plots:
        sev = p["top_severity"] if p["top_severity"] and p["top_severity"] != "info" else "none"
        r, g, b = RGB[sev]
        dim = p["id"] not in vis_ids
        rows.append({"id": p["id"], "name": p["name"], "farmer": p["farmer"], "ha": p["ha"], "variety": p["variety"], "polygon": p["polygon"], "lon": p["centroid"][0], "lat": p["centroid"][1],
                     "fill": [r, g, b, 40 if dim else 175], "line": [255, 255, 255, 255] if p["id"] != sel_id else [0, 0, 0, 255], "width": 3 if p["id"] != sel_id else 12,
                     "alerts": len([a for a in p["alerts"] if a["severity"] != "info"]), "severity": LABEL.get(p["top_severity"], "none")})
    df = pd.DataFrame(rows)
    layers = [pdk.Layer("PolygonLayer", df, id="plots", get_polygon="polygon", get_fill_color="fill", get_line_color="line", get_line_width="width", line_width_min_pixels=2,
                        pickable=True, auto_highlight=True, stroked=True, filled=True),
              pdk.Layer("ScatterplotLayer", df, id="markers", get_position="[lon, lat]", get_fill_color="fill", get_line_color="line", get_radius=40, radius_min_pixels=5, radius_max_pixels=9,
                        stroked=True, line_width_min_pixels=2, pickable=True)]
    if reps:
        rd = pd.DataFrame([{"lon": r["centroid"][0], "lat": r["centroid"][1], "label": f"{r['label']} ({r['status']})", "col": [47, 74, 31, 255] if r["status"] == "new" else [110, 138, 74, 220]}
                           for r in reps if r["status"] != "dismissed"])
        if len(rd):
            layers.append(pdk.Layer("ScatterplotLayer", rd, id="reports", get_position="[lon, lat]", get_fill_color="col", get_radius=60, radius_min_pixels=8, radius_max_pixels=14, get_line_color=[255, 255, 255], stroked=True, line_width_min_pixels=3, pickable=True))
    focus = by_id.get(sel_id)
    if focus:
        sibs = [x for x in plots if x["farmer_id"] == focus["farmer_id"]]
        lon = sum(x["centroid"][0] for x in sibs) / len(sibs)
        lat = sum(x["centroid"][1] for x in sibs) / len(sibs)
        view = pdk.ViewState(longitude=lon, latitude=lat, zoom=13, pitch=0)
    else:
        view = pdk.data_utils.compute_view([[p["centroid"][0], p["centroid"][1]] for p in plots], 0.9)
    return pdk.Deck(layers=layers, initial_view_state=view, map_provider="carto", map_style=f"{API}/basemap/satellite.json", tooltip={"html": "<b>{name}</b><br/>{farmer} · {variety} · {ha} ha<br/>Alerts: {alerts} ({severity})"}, height=520)


# ---------------- body ----------------
@st.fragment(run_every=6 if auto else None)
def body():
    recs = api_get("/assist/feedback")
    rated = {r["answer_id"]: r for r in recs if r["kind"] == "rating"}
    answers = [r for r in reversed(recs) if r["kind"] == "answer"]
    todo = [a for a in answers if a["id"] not in rated]
    tab1, tab2, tab3, tab4 = st.tabs(["Plots and rule engine", f"Grower requests ({len(open_reqs)} open)", f"Field reports ({len(new_reps)} new)",
                                      f"AI answers ({len(todo)} to review)"])
    with tab1:
        if "sel" not in st.session_state:
            st.session_state["sel"] = st.query_params.get("plot")  # deep link: ?plot=P01-1
        if st.session_state["sel"] not in by_id:
            st.session_state["sel"] = None
        left, right = st.columns([5, 4], gap="large")
        with left:
            ev = st.pydeck_chart(build_map(st.session_state["sel"]), on_select="rerun", selection_mode="single-object", key="map")
            st.caption(f"{len(vis)} of {len(plots)} plots shown · satellite imagery © Esri · click a plot or marker, or pick one below. "
                       "Red = high alert, amber = medium, green = no alert, dark pin = field report.")
            objs = (ev.selection or {}).get("objects", {}) if ev is not None else {}
            for layer in ("plots", "markers"):
                if objs.get(layer):
                    pid = objs[layer][0].get("id")
                    if pid in by_id and pid != st.session_state["sel"]:
                        st.session_state["sel"] = pid
                        st.rerun(scope="fragment")
            order = sorted(vis, key=lambda p: (-RANK.get(p["top_severity"] or "info", 0), -p["ha"]))
            tbl = pd.DataFrame([{"Plot": p["name"], "Grower": p["farmer"], "Municipality": p["municipality"], "ha": p["ha"], "Variety": p["variety"],
                                 "Top alert": LABEL.get(p["top_severity"], "–") if p["top_severity"] != "info" else "–",
                                 "Pending": len([a for a in p["alerts"] if a["severity"] != "info" and not a["review"]])} for p in order])
            if len(tbl):
                sel = st.dataframe(tbl, hide_index=True, width="stretch", on_select="rerun", selection_mode="single-row", height=260, key="tbl")
                rows = (sel.selection or {}).get("rows", []) if sel is not None else []
                if rows and order[rows[0]]["id"] != st.session_state["sel"]:
                    st.session_state["sel"] = order[rows[0]]["id"]
                    st.rerun(scope="fragment")
            if st.button("Validate all pending alerts shown", help="Records that you reviewed each pending alert in the current filter."):
                todo = [a for p in vis for a in p["alerts"] if a["severity"] != "info" and not a["review"] and not a.get("community")]
                for a in todo:
                    api_post("/review/" + a["id"], {"status": "validated", "note": "Batch validated"})
                st.toast(f"{len(todo)} validated.")
                st.rerun()
        with right:
            p = by_id.get(st.session_state["sel"])
            if not p:
                st.info("Select a plot on the map or in the table to see the rule engine's proposed actions, the weather time series, and to validate.")
            else:
                st.subheader(f"{p['name']}  ·  {p['farmer']}")
                st.caption(f"{p['farm']} · {p['municipality']}, {p['province']}")
                f1, f2, f3, f4 = st.columns(4)
                f1.metric("Area", f"{p['ha']} ha")
                f2.metric("Variety", p["variety"])
                f3.metric("Irrigation", p["irrigation"].replace(" irrigation", ""))
                f4.metric("Altitude", f"{p['altitude_m']} m" if p["altitude_m"] else "–")
                st.caption(f"SIGPAC `{p['sigpac_ref']}` · slope {p['slope_pct']}% · attributes: {p['attrs_source']}")
                st.markdown(f"##### Rule engine output · {date.fromisoformat(clock):%a %d %b %Y}")
                als = sorted(p["alerts"], key=lambda a: -RANK[a["severity"]])
                if not als:
                    st.success("No rule fired for this plot today.")
                for i, a in enumerate(als):
                    alert_card(a, f"{p['id']}-{i}-{clock}")
        if p:
            st.divider()
            weather_panel(p)
    with tab2:
        if not reqs:
            st.info("No requests yet. Farmers send them from the app with “Ask Elena to check this”.")
        by_f = {x["farmer_id"]: x for x in plots}
        for r in reqs:
            f = by_f.get(r["farmer_id"], {})
            with st.expander(f"{'🟢 Review asked' if r['status'] == 'asked' else '✔ Answered'} · {f.get('farmer', r['farmer_id'])} · {r['title']} · {r['urgency']}", expanded=r["status"] == "asked"):
                st.markdown(f"**Their question** ({r['created_at']}): {r['message']}")
                if r["photos"]:
                    cols = st.columns(max(len(r["photos"]), 3))
                    for col, ph in zip(cols, r["photos"], strict=False):
                        b = thumb_bytes(ph.get("thumb"))
                        if b:
                            col.image(b, caption=ph["label"])
                        else:
                            col.caption(f"📷 {ph['label']}")
                st.caption("Field data shared" if r["share_data"] else "Field data not shared")
                for x in r["replies"]:
                    st.markdown(f"> **You** ({x.get('decision') or 'reply'}): {x['text']}")
                al = next((a for p in plots for a in p["alerts"] if a["id"] == r["alert_id"]), None)
                if al and r["status"] == "asked":
                    alert_card(al, f"req-{r['id']}", request_id=r["id"])
                elif not al and r["status"] == "asked":
                    st.warning(f"The alert behind this request is not active on {clock}. Move the replay date to {r['clock_date']}.")
    with tab3:
        if not reps:
            st.info("No field reports yet.")
        for r in reps:
            p = by_id.get(r["parcel_id"], {})
            with st.container(border=True):
                st.markdown(f"**{r['label']} · {r['municipality']}**  :{'orange' if r['status'] == 'new' else 'green' if r['status'] == 'verified' else 'gray'}-badge[{r['status']}]")
                st.caption(f"{p.get('farmer', '')} · {r['created_at']} · {'may warn nearby growers' if r['visibility'] == 'nearby' else 'advisor only'}")
                st.write(r["notes"])
                if r["status"] == "new":
                    a, b = st.columns(2)
                    if a.button("Verify" + (" and warn area" if r["visibility"] == "nearby" else ""), key=f"vr-{r['id']}", type="primary"):
                        api_post(f"/reports/{r['id']}/verify", {"action": "verify"})
                        st.toast("Verified. Nearby growers warned without the reporter's name.")
                        st.rerun()
                    if b.button("Dismiss", key=f"dr-{r['id']}"):
                        api_post(f"/reports/{r['id']}/verify", {"action": "dismiss"})
                        st.rerun()
                elif r["status"] == "verified" and r.get("warned_farmers") is not None:
                    st.caption(f"{len(r['warned_farmers'])} grower(s) within {r.get('radius_km', 10)} km warned.")
    with tab4:
        st.caption("Answers the assistant gave to growers. Your verdict teaches it: good and corrected answers become examples for similar questions; bad ones are never reused.")
        if not answers:
            st.info("No assistant answers yet. Ask a question on an alert in the farmer app.")
        for a in answers[:30]:
            r = rated.get(a["id"])
            with st.container(border=True):
                badge = f":{'green' if r['verdict'] == 'good' else 'orange' if r['verdict'] == 'corrected' else 'red'}-badge[{r['verdict']}]" if r else ":gray-badge[to review]"
                st.markdown(f"**{a['question']}** {badge}")
                st.write(a["answer"])
                st.caption(f"{a['at']} · {a['backend']} · rules: {', '.join(a['cites'][:3])}")
                if r:
                    if r["corrected"]:
                        st.markdown(f"**Corrected by {r['advisor']}:** {r['corrected']}")
                    continue
                fix = st.text_area("Better answer (optional)", key=f"fx-{a['id']}", height=70)
                c1, c2, c3 = st.columns(3)
                for col, verdict, label in ((c1, "good", "Good"), (c2, "corrected", "Save my correction"), (c3, "bad", "Bad")):
                    if col.button(label, key=f"{verdict}-{a['id']}", type="primary" if verdict == "good" else "secondary",
                                  disabled=verdict == "corrected" and not fix.strip()):
                        api_post("/assist/feedback", {"answer_id": a["id"], "verdict": verdict, "corrected": fix.strip() if verdict == "corrected" else ""})
                        st.rerun()


body()
