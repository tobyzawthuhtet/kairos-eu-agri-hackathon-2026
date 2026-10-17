from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import advisories, alerts, farms, replay

app = FastAPI(title="Kairos")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])
app.include_router(replay.router, tags=["replay"])
app.include_router(farms.router, prefix="/farms", tags=["farms"])
app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
app.include_router(advisories.router, prefix="/advisories", tags=["advisories"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
