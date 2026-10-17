"""Build demo growers and plots from real LPIS (SIGPAC) olive parcels in Jaén and Córdoba.

Real:   parcel geometry, area (dn_surface), SIGPAC reference, slope, altitude, irrigation coefficient.
Demo:   grower names, farm names, plot names, varieties, advisor. Fictional, deterministic (seeded).
Hook:   if data/raw/olive_dataset/*.csv exists it is joined on the SIGPAC reference and overrides variety,
        irrigation, planting year, etc. (see apply_external_attributes).

Outputs: data/processed/demo/farms.json and data/processed/demo/cell_features.csv.gz
         (daily ERA5-Land features for the 0.1 deg cells the plots sit in, 2025).
"""
import json
import random
import tempfile
import warnings
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr

from kairos.features.era5_features import daily_cell_features

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/processed/demo"
LPIS = ROOT / "data/raw/lpis/2026/andalucia"
GRID = 0.1
MUNI = pd.read_csv(ROOT / "configs/municipalities.csv", dtype=str).set_index("code")["name"].to_dict()
MUNIS = ["23061", "23009", "23092", "23060", "23087", "23069", "23005",
         "14007", "14043", "14055", "14049", "14019", "14056"]
VARIETIES = ["Picual", "Picual", "Picual", "Arbequina", "Hojiblanca", "Cornicabra"]
PLOT_NAMES = ["Cerro Alto", "La Solana", "El Pozo", "Los Almendros", "La Umbría", "El Llano", "Vega Baja", "Los Pinos",
              "La Dehesa", "El Mirador", "Cañada Honda", "Las Peñuelas", "El Calvario", "La Fuensanta", "Los Chaparros",
              "Cuesta Larga", "El Olivar Viejo", "La Atalaya", "Fuente Seca", "Los Álamos", "El Portichuelo", "La Cañada", "Los Cerrillos",
              "El Peñón", "La Fresneda", "Majada Alta", "El Tomillar", "Las Zorreras", "Los Naranjos", "El Hornillo", "Casa Blanca",
              "La Rinconada", "El Cortijuelo", "Valdecuevas", "La Hoya", "Los Barrancos", "El Alcornocal", "Torre Alta", "La Mimbre",
              "Cerro Gordo", "El Espino", "La Tejera", "Los Villares", "El Pedregal", "La Zarza", "Las Hazas", "El Rodeo", "Los Cantos",
              "La Alberca", "El Bujeo", "Vistahermosa"]
FIRST = ["Juan", "Antonio", "Carmen", "Manuel", "Lucía", "José", "María", "Francisco", "Pilar", "Rafael", "Dolores", "Miguel",
         "Teresa", "Pedro", "Rosario", "Luis", "Ana", "Diego", "Isabel", "Alberto", "Marta", "Sergio", "Inés", "Pablo"]
LAST = ["Morales", "Reyes", "Ortega", "Cano", "Navas", "Molina", "Quesada", "Ruiz", "Serrano", "Lara", "Muñoz", "Aranda",
        "Cobo", "Expósito", "Peña", "Garrido", "Cuenca", "Soler", "Ibáñez", "Villar", "Bravo", "Arjona", "Ramos", "Torres"]
FARM_PREFIX = ["Finca", "Olivares", "Cortijo", "Hacienda", "Finca", "Olivar"]
SPECS = [  # (grower, farm, municipality, [(target_ha, variety, plot name, must_be_irrigated)])
    ("Juan Morales", "Finca El Cerro", "23061", [(14.5, "Picual", "Cerro Alto", True), (8.2, "Arbequina", "La Solana", True), (5.3, "Picual", "El Pozo", True)]),
    ("Antonio Reyes", "Olivares Reyes", "14043", [(22, "Picual", "Los Almendros", True), (11, "Picual", "El Llano", False), (8, "Hojiblanca", "Vega Baja", False)]),
    ("Carmen Ortega", "Finca La Umbría", "23009", [(10, "Hojiblanca", "La Umbría", True), (6, "Hojiblanca", "El Mirador", False), (3, "Picual", "Los Pinos", False)]),
]


def read_olive(muni: str) -> gpd.GeoDataFrame:
    prov = muni[:2]
    zp = next((LPIS / prov).glob(f"{muni}_rec_*.zip"))
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zp) as z:
            z.extract(next(n for n in z.namelist() if n.endswith(".gpkg")), tmp)
        g = gpd.read_file(next(Path(tmp).glob("*.gpkg")), layer="recinto")
    g = g[(g["uso_sigpac"] == "OV") & (g["dn_surface"] >= 8000)].copy()
    g["ha"] = g["dn_surface"] / 1e4
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        c = g.geometry.centroid
    g["clon"], g["clat"] = c.x, c.y
    g["muni"] = muni
    return g.reset_index(drop=True)


def sigpac_ref(r) -> str:
    return f"{int(r.provincia):02d}:{int(r.municipio):03d}:{int(r.agregado)}:{int(r.zona)}:{int(r.poligono)}:{int(r.parcela)}:{int(r.recinto)}"


def pick(pool: gpd.GeoDataFrame, used: set, anchor, target: float, irrigated: bool | None, radius_deg: float):
    cand = pool[~pool.index.isin(used)]
    if anchor is not None:
        cand = cand[np.hypot(cand.clon - anchor[0], cand.clat - anchor[1]) <= radius_deg]
    if irrigated is True:
        cand = cand[cand.coef_regadio.fillna(0) > 0]
    elif irrigated is False:
        cand = cand[cand.coef_regadio.fillna(0) == 0]
    if cand.empty:
        return None
    return cand.loc[(cand.ha - target).abs().idxmin()]


def simplify_ring(geom) -> list:
    g = geom.simplify(0.00008, preserve_topology=True)
    poly = max(g.geoms, key=lambda p: p.area) if g.geom_type == "MultiPolygon" else g
    return [[round(x, 5), round(y, 5)] for x, y in poly.exterior.coords]


def build_farms() -> tuple[list[dict], set]:
    rng = random.Random(20)
    pools = {m: read_olive(m) for m in MUNIS}
    used: dict[str, set] = {m: set() for m in MUNIS}
    names = [f"{f} {rng.choice(LAST)}" for f in FIRST]
    specs = list(SPECS)
    weights = {"23061": 6, "23009": 2, "23092": 2, "23060": 2, "23087": 2, "23069": 1, "23005": 1, "14007": 2, "14043": 2, "14055": 1, "14049": 1, "14019": 1}
    munis_cycle = [m for m, w in weights.items() for _ in range(w)]
    rng.shuffle(munis_cycle)
    for i in range(len(specs), 24):
        n = rng.choice([1, 2, 2, 3])
        tot = rng.choice([6, 9, 12, 16, 22, 30, 38])
        parts = [tot * w / sum(range(1, n + 1)) for w in range(n, 0, -1)]
        muni = munis_cycle[i % len(munis_cycle)]
        gname = names[i] if i < len(names) else f"{rng.choice(FIRST)} {rng.choice(LAST)}"
        farm = f"{rng.choice(FARM_PREFIX)} {rng.choice(['La Vega', 'El Cerro', 'La Solana', 'La Umbría', 'La Noria', 'La Alameda', 'La Retama', 'La Fuente', 'Las Lomas', 'Los Llanos'])}"
        specs.append((gname, farm, muni, [(p, rng.choice(VARIETIES), "", rng.random() < 0.5) for p in parts]))
    farmers, cells = [], set()
    plot_names = PLOT_NAMES.copy()
    for fi, (gname, farm, muni, plots) in enumerate(specs):
        pool, anchor, parcels = pools[muni], None, []
        for target, variety, pname, irr in plots:
            r = pick(pool, used[muni], anchor, target, irr, 0.06 if anchor else 9)
            if r is None:
                r = pick(pool, used[muni], anchor, target, None, 0.06 if anchor else 9)
            if r is None:
                continue
            used[muni].add(r.name)
            anchor = anchor or (r.clon, r.clat)
            irrigated = bool((r.coef_regadio or 0) > 0)
            name = pname or (plot_names.pop(rng.randrange(len(plot_names))) if plot_names else f"Parcela {len(parcels) + 1}")
            cell = (round(round(r.clat / GRID) * GRID, 1), round(round(r.clon / GRID) * GRID, 1))
            cells.add(cell)
            parcels.append({
                "id": f"P{fi + 1:02d}-{len(parcels) + 1}", "name": name, "sigpac_ref": sigpac_ref(r), "ha": round(float(r.ha), 1),
                "variety": variety, "irrigation": "drip irrigation" if irrigated else "rainfed",
                "irrigation_coef": float(r.coef_regadio or 0), "slope_pct": None if pd.isna(r.pendiente_media) else round(r.pendiente_media / 10, 1),
                "altitude_m": None if pd.isna(r.altitud) else int(r.altitud), "centroid": [round(r.clon, 5), round(r.clat, 5)],
                "cell": list(cell), "polygon": simplify_ring(r.geometry), "attrs_source": "demo (variety) + LPIS (area, geometry, slope, altitude, irrigation)"})
        if not parcels:
            continue
        words = gname.split()
        farmers.append({"id": f"F{fi + 1:02d}", "name": gname, "initials": (words[0][0] + words[-1][0]).upper(), "farm": farm,
                        "municipality": MUNI[muni], "place": {"F01": "Jaén", "F02": "Córdoba"}.get(f"F{fi + 1:02d}", MUNI[muni]), "municipality_code": muni, "province": "Jaén" if muni.startswith("23") else "Córdoba",
                        "province_code": muni[:2], "ha": round(sum(p["ha"] for p in parcels), 1), "advisor_id": "A01", "parcels": parcels})
    return farmers, cells


def apply_external_attributes(farmers: list[dict]) -> int:
    """Join a user-supplied olive dataset (data/raw/olive_dataset/*.csv) on the SIGPAC reference."""
    files = sorted((ROOT / "data/raw/olive_dataset").glob("*.csv")) if (ROOT / "data/raw/olive_dataset").exists() else []
    if not files:
        return 0
    ext = pd.concat([pd.read_csv(f, dtype=str) for f in files])
    ext.columns = [c.strip().lower() for c in ext.columns]
    key = next((c for c in ("sigpac_ref", "sigpac", "refcat", "ref") if c in ext.columns), None)
    if not key:
        print("external dataset has no SIGPAC reference column; skipped")
        return 0
    ext = ext.set_index(key)
    n = 0
    for f in farmers:
        for p in f["parcels"]:
            if p["sigpac_ref"] in ext.index:
                row = ext.loc[p["sigpac_ref"]]
                row = row.iloc[0] if isinstance(row, pd.DataFrame) else row
                for col in ("variety", "irrigation", "planting_year", "tree_density", "yield_kg_ha"):
                    if col in row and pd.notna(row[col]):
                        p[col] = row[col]
                p["attrs_source"] = "external olive dataset"
                n += 1
    return n


def cell_features(cells: set) -> pd.DataFrame:
    lat = xr.DataArray([c[0] for c in sorted(cells)], dims="cell")
    lon = xr.DataArray([c[1] for c in sorted(cells)], dims="cell")
    land = ROOT / "data/raw/climate/reanalysis-era5-land/spain"
    sl = ROOT / "data/raw/climate/reanalysis-era5-single-levels/spain"
    frames = []
    for ym in pd.period_range("2025-01", "2025-12", freq="M").astype(str):
        lf, gf = sorted(land.glob(f"{ym}_g*.nc")), sorted(sl.glob(f"{ym}_g*.nc"))
        if not lf:
            continue
        with xr.open_mfdataset(lf, combine="by_coords") as ds:
            sub = ds.sel(latitude=lat, longitude=lon, method="nearest", tolerance=0.06).load()
        res = daily_cell_features(sub, pev=sub if "pev" in sub else None)
        if gf:
            with xr.open_mfdataset(gf, combine="by_coords") as g:
                gv = g[next(v for v in g.data_vars)].sel(latitude=lat, longitude=lon, method="nearest").load()
            gt = "valid_time" if "valid_time" in gv.dims else "time"
            res["gust_max_ms"] = gv.resample({gt: "1D"}).max().rename({gt: "date"})
        df = res.to_dataframe().reset_index()
        df["cell_lat"] = lat.values[df["cell"]]
        df["cell_lon"] = lon.values[df["cell"]]
        frames.append(df.drop(columns=[c for c in ("cell", "latitude", "longitude", "number", "expver") if c in df]))
        print(ym, flush=True)
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    farmers, cells = build_farms()
    joined = apply_external_attributes(farmers)
    advisor = {"id": "A01", "name": "Elena Navarro", "initials": "EN", "title": "Olive advisor", "reply_hours": 4,
               "area": "Jaén and Córdoba"}
    (OUT / "farms.json").write_text(json.dumps({"advisor": advisor, "farmers": farmers}, ensure_ascii=False))
    print(f"{len(farmers)} growers, {sum(len(f['parcels']) for f in farmers)} plots, {len(cells)} ERA5 cells, external rows joined: {joined}")
    cell_features(cells).to_csv(OUT / "cell_features.csv.gz", index=False)
    print("cell features written")


if __name__ == "__main__":
    main()
