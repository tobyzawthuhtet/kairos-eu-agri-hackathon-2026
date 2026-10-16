"""Daily agro-climate features from ERA5-Land hourly data, aggregated to olive-weighted province series.

Inputs are the NetCDF files written by scripts/download_era5.py. Features map to decision-table drivers:
temperature (frost/heat/chill/GDD), leaf_wetness_rh (wetness-hour proxy), precipitation, soil_moisture,
soil_temp, wind_gust, potential_evap.

Caveats (documented, not hidden):
- ERA5-Land tp / pev are accumulated since 00 UTC; we de-accumulate. The first hour of each monthly file
  and the last hour of the month are lost (<=2 h/month), so month-edge daily totals can be ~4% low.
- Wetness is a PROXY (hours with RH >= RH_WET and rain-free or wet), not measured leaf wetness.
- Chill UNITS (De Melo-Abreu model) are not implemented: only hours below 7 °C. TODO with agronomist.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

T_BASE_GDD = 9.1  # °C, decision table OLV-S03-PHEN
CHILL_T = 7.0  # °C, decision table OLV-S01-CHILL-05..08
RH_WET = 90.0  # % (table says >=98 % for infection; ERA5 9 km smooths humidity, so a lower proxy is used)


def _tname(ds: xr.Dataset) -> str:
    return "valid_time" if "valid_time" in ds.dims else "time"


def _deaccumulate(da: xr.DataArray, t: str) -> xr.DataArray:
    """ERA5-Land accumulations (since 00 UTC) -> per-hour amounts."""
    diff = da.diff(t)
    hours = da[t].dt.hour
    inc = xr.where(hours.isel({t: slice(1, None)}) == 1, da.isel({t: slice(1, None)}), diff)
    return inc.clip(min=0)


def rh_percent(t_c: xr.DataArray, td_c: xr.DataArray) -> xr.DataArray:
    """Magnus formula."""
    a, b = 17.625, 243.04
    return (100 * np.exp(a * td_c / (b + td_c)) / np.exp(a * t_c / (b + t_c))).clip(0, 100)


def daily_cell_features(ds: xr.Dataset, gust: xr.Dataset | None = None, pev: xr.Dataset | None = None) -> xr.Dataset:
    """Hourly ERA5-Land -> daily features per grid cell."""
    t = _tname(ds)
    tc = ds["t2m"] - 273.15
    td = ds["d2m"] - 273.15
    rh = rh_percent(tc, td)
    rain = _deaccumulate(ds["tp"], t) * 1000.0  # m -> mm per hour (aligned from 2nd timestep)
    tc2, rh2 = tc.isel({t: slice(1, None)}), rh.isel({t: slice(1, None)})
    wet = (rh2 >= RH_WET) | (rain > 0.1)
    out = {
        "tmin_c": tc.resample({t: "1D"}).min(),
        "tmax_c": tc.resample({t: "1D"}).max(),
        "tmean_c": tc.resample({t: "1D"}).mean(),
        "rh_mean_pct": rh.resample({t: "1D"}).mean(),
        "rh_min_pct": rh.resample({t: "1D"}).min(),
        "precip_mm": rain.resample({t: "1D"}).sum(),
        "precip_max_12h_mm": rain.rolling({t: 12}).sum().resample({t: "1D"}).max(),
        "chill_hours_lt7": (tc < CHILL_T).resample({t: "1D"}).sum(),
        "gdd_base9_1": (np.maximum(tc - T_BASE_GDD, 0)).resample({t: "1D"}).mean(),
        # hours wet AND between 8 and 24 °C: infection-favourable (peacock spot / anthracnose proxy)
        "wet_hours_8_24c": (wet & (tc2 >= 8) & (tc2 <= 24)).resample({t: "1D"}).sum(),
        "soil_moisture_l1": ds["swvl1"].resample({t: "1D"}).mean(),
        "soil_moisture_l2": ds["swvl2"].resample({t: "1D"}).mean(),
        "soil_moisture_l3": ds["swvl3"].resample({t: "1D"}).mean(),
        "soil_temp_l1_c": (ds["stl1"] - 273.15).resample({t: "1D"}).mean(),
        "soil_temp_l2_c": (ds["stl2"] - 273.15).resample({t: "1D"}).mean(),
    }
    res = xr.Dataset(out).rename({t: "date"})
    if pev is not None:
        pt = _tname(pev)
        res["pev_mm"] = (-_deaccumulate(pev["pev"], pt) * 1000.0).resample({pt: "1D"}).sum().rename({pt: "date"})
    if gust is not None:
        gt = _tname(gust)
        g = gust[next(v for v in gust.data_vars if "gust" in v.lower() or v == "i10fg")]
        res["gust_max_ms"] = g.resample({gt: "1D"}).max().rename({gt: "date"})
    return res


def province_series(cell_daily: xr.Dataset, weights: pd.DataFrame) -> pd.DataFrame:
    """Olive-area-weighted mean of daily cell features. weights: columns lat, lon, olive_ha (one province)."""
    w = weights.groupby(["lat", "lon"], as_index=False)["olive_ha"].sum()
    lat = xr.DataArray(w["lat"].values, dims="cell")
    lon = xr.DataArray(w["lon"].values, dims="cell")
    sel = cell_daily.sel(latitude=lat, longitude=lon, method="nearest", tolerance=0.06)
    wt = xr.DataArray(w["olive_ha"].values, dims="cell")
    out = {}
    for v in sel.data_vars:
        ok = sel[v].notnull()
        out[v] = ((sel[v] * wt).where(ok).sum("cell") / wt.where(ok).sum("cell")).to_series()
    return pd.DataFrame(out)


def open_month(path: Path) -> xr.Dataset:
    return xr.open_dataset(path)
