"""Farmer-friendly wording for engine hazards. Titles/summaries only; thresholds come from the decision table."""

TITLE = {
    "heat": "Heat stress on {plot}", "frost": "Frost risk on {plot}", "frost_inflorescence": "Frost on the flower buds at {plot}",
    "cold_warning": "Cold night at {plot}", "wind": "Strong wind expected at {plot}", "wind_hot_dry": "Hot, dry wind at {plot}",
    "peacock_spot_infection": "Peacock spot weather at {plot}", "heavy_rain": "Heavy rain at {plot}",
    "olive_fly_heat_suppression": "Heat is slowing the olive fly at {plot}", "saissetia_heat_mortality": "Heat is killing young black scale at {plot}",
    "verticillium": "Warm soil: watch for verticillium at {plot}", "soil_drying": "Soil drying fast on {plot}",
    "rain_ahead": "Rain on {day}: {mm} mm expected", "water_use": "Water use at {pct}% of plan",
}
KIND = {"heat": "weather", "frost": "weather", "frost_inflorescence": "weather", "cold_warning": "weather", "wind": "weather",
        "wind_hot_dry": "weather", "peacock_spot_infection": "weather", "heavy_rain": "weather", "olive_fly_heat_suppression": "weather",
        "saissetia_heat_mortality": "weather", "verticillium": "weather", "soil_drying": "irrigation", "rain_ahead": "irrigation",
        "water_use": "irrigation"}
SUMMARY = {
    "heat": "Daytime high reached {value:g} °C ({op} {threshold} °C).", "frost": "Night low fell to {value:g} °C ({op} {threshold} °C).",
    "frost_inflorescence": "Night low fell to {value:g} °C while buds are developing ({op} {threshold} °C).",
    "cold_warning": "Night low of {value:g} °C ({op} {threshold} °C).", "wind": "Gusts reached {value:g} km/h ({op} {threshold} km/h).",
    "wind_hot_dry": "Gusts reached {value:g} km/h in the flower-bud stage.",
    "peacock_spot_infection": "{value:g} hours of leaf wetness at mild temperatures, enough for infection.",
    "heavy_rain": "{value:g} mm in 12 hours ({op} {threshold} mm).",
    "olive_fly_heat_suppression": "Highs of {value:g} °C slow fly activity.", "saissetia_heat_mortality": "Hot, dry air ({value:g} °C) kills young scale.",
    "verticillium": "Soil at {value:g} °C is in the range verticillium likes.",
}
SEV_UI = {"info": "Info", "low": "Low", "moderate": "Medium", "high": "High", "severe": "High"}
