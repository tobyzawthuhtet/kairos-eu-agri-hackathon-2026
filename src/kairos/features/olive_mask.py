"""Olive-area weights on the ERA5 0.1° grid, built from SIGPAC (LPIS) recintos.

Crop-agnostic: pass another crop's SIGPAC use codes/weights to reuse for other crops.
SIGPAC uso codes: OV olivar (1.0); mixed OF, OC, VO, FL counted at MIXED_WEIGHT (assumption).
"""
import tempfile
import warnings
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd

OLIVE_USES = {"OV": 1.0, "OF": 0.5, "OC": 0.5, "VO": 0.5, "FL": 0.5}
GRID = 0.1  # ERA5-Land resolution, cell centres at multiples of 0.1°


def zip_to_cells(zip_path: Path, uses: dict[str, float] = OLIVE_USES) -> pd.DataFrame:
    """One municipality GPKG zip -> DataFrame[province, lat, lon, olive_ha] on the ERA5 grid."""
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zip_path) as z:
            z.extract(next(n for n in z.namelist() if n.endswith(".gpkg")), tmp)
        gpkg = next(Path(tmp).glob("*.gpkg"))
        g = gpd.read_file(gpkg, layer="recinto", columns=["provincia", "dn_surface", "uso_sigpac"])
    g = g[g["uso_sigpac"].isin(uses)]
    if g.empty:
        return pd.DataFrame(columns=["province", "lat", "lon", "olive_ha"])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # centroid in geographic CRS is fine at parcel scale
        c = g.geometry.centroid
    out = pd.DataFrame({
        "province": g["provincia"].astype(int).map("{:02d}".format),
        "lat": (c.y / GRID).round() * GRID,
        "lon": (c.x / GRID).round() * GRID,
        "olive_ha": g["dn_surface"] / 1e4 * g["uso_sigpac"].map(uses),  # dn_surface is m²
    })
    out[["lat", "lon"]] = out[["lat", "lon"]].round(1)
    return out.groupby(["province", "lat", "lon"], as_index=False)["olive_ha"].sum()
