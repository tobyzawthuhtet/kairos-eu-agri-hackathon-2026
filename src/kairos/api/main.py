from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routes import advisories, alerts, demo, farms, replay

app = FastAPI(title="Kairos")


@app.on_event("startup")
def _warm_llm() -> None:
    import threading

    from kairos.assist import llm

    threading.Thread(target=llm.warm, daemon=True).start()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])
app.include_router(replay.router, tags=["replay"])
app.include_router(demo.router, prefix="/demo", tags=["demo"])
app.include_router(farms.router, prefix="/farms", tags=["farms"])
app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
app.include_router(advisories.router, prefix="/advisories", tags=["advisories"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


# static front ends (farmer app, advisor app; the advisor dashboard is Streamlit, see demo/dashboard_app.py), served next to the API so one command runs the demo
_DEMO = Path(__file__).resolve().parents[3] / "demo"
for _name in ("farmer", "advisor", "shared"):
    if (_DEMO / _name).exists():
        app.mount(f"/{_name}", StaticFiles(directory=_DEMO / _name, html=True), name=_name)
