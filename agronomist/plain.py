"""Plain-language wording for decision-table scenarios, so a non-programmer can check them."""
import re

STAGE = {"dormancy_chilling": "Dormancy and winter chill", "budbreak_shoot_growth": "Bud break and shoot growth", "inflorescence_development": "Flower-bud development",
         "flowering_anthesis": "Flowering", "fruit_set": "Fruit set", "pit_hardening": "Pit hardening", "fruit_growth_oil_accumulation": "Fruit growth and oil build-up",
         "ripening_harvest": "Ripening and harvest", "post_harvest_recovery": "After harvest"}
STAGE_ORDER = list(STAGE)
VAR = [(r"^(Tmin_2m|air_temperature_min)", "the lowest air temperature"), (r"^(tmax|Tmax|air_temperature_max)", "the highest air temperature"),
       (r"precip.*12h|precipitation_accumulated_12h", "the rain that falls in 12 hours"), (r"precipitation_accumulated_1h", "the rain that falls in 1 hour"),
       (r"gust|wind_gust", "the strongest wind gust"), (r"leaf_wetness", "the hours the leaves stay wet"), (r"soil_temp", "the soil temperature"),
       (r"chill", "the winter chill accumulated since 1 October"), (r"GDD", "the heat accumulated since dormancy ended"), (r"swp_midday", "midday stem water potential (a field measurement)"),
       (r"punctured_fruit", "the share of olives punctured by fly (a field count)"), (r"storm_hail", "the hail stone size (an event report)"), (r"^air_temperature", "the air temperature")]
OP = {"<=": "is at or below", "<": "is below", ">=": "is at or above", ">": "is above", "between": "is between", "==": "is"}
SEV = {"l": "Low", "low": "Low", "m": "Medium", "medium": "Medium", "h": "High", "high": "High", "critical": "Critical", "info": "Info"}
CONF = {"l": "low", "low": "low", "m": "medium", "medium": "medium", "h": "high", "high": "high"}


def var_words(v: str) -> str:
    return next((w for pat, w in VAR if re.search(pat, v)), v.replace("_", " "))


def unit(u: str) -> str:
    return {"C": " °C", "%": " %"}.get(u, f" {u}" if u and u != "NAV" else "")


def sentence(r: dict, threshold: str | None = None) -> str:
    thr = threshold if threshold is not None else r["threshold"]
    if thr in ("", "NAV"):
        cond = f"{var_words(r['variable'])} reaches a level that the sources do not give yet"
    else:
        cond = f"{var_words(r['variable'])} {OP.get(r['operator'], r['operator'])} {thr}{unit(r['unit'])}"
    dur = r["duration"]
    extra = ""
    if dur and dur not in ("NAV", "1 d", "gust", "season") and len(dur) < 40:
        extra = f", {dur}" if dur.lower().startswith(("at ", "with ", "when ", "after ", "during ")) else f", for {dur}"
    return f"During {STAGE.get(r['stage'].split('|')[0], r['stage']).lower()}{' (and later stages)' if '|' in r['stage'] else ''}, when {cond}{extra}, Kairos warns the grower."
