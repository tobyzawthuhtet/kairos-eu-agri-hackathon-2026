from datetime import date, timedelta

from fastapi.testclient import TestClient

from kairos.alerts.generator import generate_alerts
from kairos.api.main import app
from kairos.config import load_crop, load_regions
from kairos.schemas import DailyObservation, Hazard


def _heat_wave(days=4, tmax=41.0):
    start = date(2026, 7, 1)
    return [DailyObservation(farm_id="f1", day=start + timedelta(i), tmax_c=tmax) for i in range(days)]


def test_configs_load():
    assert load_crop("olive")["crop"] == "olive"
    assert load_regions()


def test_heat_wave_alert():
    alerts = generate_alerts(_heat_wave())
    assert alerts and alerts[0].hazard is Hazard.heat


def test_no_alert_when_mild():
    assert generate_alerts(_heat_wave(tmax=25.0)) == []


def test_health():
    assert TestClient(app).get("/health").json() == {"status": "ok"}
