import pandas as pd

from kairos.rules.table_engine import (
    active_stages,
    evaluate,
    load_ruleset,
    parse_regions,
    top_per_hazard,
)


def _frame(**cols):
    idx = pd.date_range("2025-05-20", periods=3)
    base = {"tmin_c": 10.0, "tmax_c": 25.0, "tmean_c": 18.0, "rh_min_pct": 40.0, "precip_max_12h_mm": 0.0,
            "wet_hours_8_24c": 0.0, "gust_max_ms": 5.0, "soil_temp_l1_c": 20.0}
    base.update(cols)
    return pd.DataFrame({k: [v] * 3 if not isinstance(v, list) else v for k, v in base.items()}, index=idx)


def test_regions_parsed_from_free_text():
    assert parse_regions("Andalucia;Castilla-La Mancha") == {"andalucia", "castilla_la_mancha"}
    assert parse_regions("ES-AN|ES-CT") == {"andalucia", "cataluna"}


def test_hot_flowering_day_fires_heat_rule():
    a = evaluate(_frame(tmax_c=[25.0, 36.0, 25.0]), "andalucia")
    heat = a[(a["hazard"] == "heat") & (a["date"] == "2025-05-21")]
    assert not heat.empty and set(heat["severity"]) <= {"low", "moderate", "high", "severe"}
    assert a[(a["hazard"] == "heat") & (a["date"] == "2025-05-20")].empty


def test_top_per_hazard_keeps_most_severe():
    a = top_per_hazard(evaluate(_frame(tmax_c=[25.0, 41.0, 25.0]), "andalucia"))
    heat = a[(a["hazard"] == "heat") & (a["date"] == "2025-05-21")]
    assert len(heat) == 1 and heat.iloc[0]["severity"] in {"high", "severe"}


def test_non_weather_rows_reported_not_dropped():
    rs = load_ruleset()
    reasons = {x["reason"] for x in rs.not_evaluable}
    assert "needs field scouting or a sample count" in reasons
    assert len(rs.rules) + len(rs.not_evaluable) == 142


def test_stage_calendar():
    from datetime import date
    assert "flowering_anthesis" in active_stages(date(2025, 5, 10))
    assert "dormancy_chilling" in active_stages(date(2025, 1, 10))
