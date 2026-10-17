"""Core data contracts shared across pipeline stages and the API."""
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class Severity(str, Enum):
    info = "info"
    low = "low"
    moderate = "moderate"
    high = "high"
    severe = "severe"


class Hazard(str, Enum):
    heat = "heat"
    drought = "drought"
    frost = "frost"
    pest_disease = "pest_disease"


class Farm(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    crop: str = "olive"
    area_ha: float | None = None


class DailyObservation(BaseModel):
    """Fused, farm-level daily record (after alignment + bias correction)."""
    farm_id: str
    day: date
    tmax_c: float | None = None
    tmin_c: float | None = None
    tmean_c: float | None = None
    humidity_pct: float | None = None
    precip_mm: float | None = None
    soil_moisture: float | None = None
    ndvi: float | None = None
    ndvi_baseline: float | None = None


class RiskAssessment(BaseModel):
    farm_id: str
    hazard: Hazard
    severity: Severity
    score: float = Field(ge=0, le=1)
    rationale: str


class Alert(BaseModel):
    farm_id: str
    hazard: Hazard
    severity: Severity
    title: str
    action: str                      # e.g. "Irrigate within 48h"
    created_at: datetime
    reviewed_by: str | None = None   # agronomist sign-off (human link)
    approved: bool = False
