from fastapi import FastAPI

from .routes import advisories, alerts, farms

app = FastAPI(title="Kairos")
app.include_router(farms.router, prefix="/farms", tags=["farms"])
app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
app.include_router(advisories.router, prefix="/advisories", tags=["advisories"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
