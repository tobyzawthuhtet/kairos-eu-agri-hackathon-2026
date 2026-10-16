#!/usr/bin/env python3
"""Extract olive field observations from RAIF Andalucia end-of-campaign PDFs.

Input : data/raw/ground_truth/raif/*.pdf   (RAIF "Informe de Especial Interes Olivar",
        provincial and autonomic end-of-campaign balances; Spanish prose + figures)
Output: data/processed/ground_truth/raif_olive_labels.csv  (LONG format, one
        observation per row)

Run:  uv run python scripts/extract_raif.py [--raw DIR] [--out CSV] [--years 2022-2025]

Metrics emitted (column `metric`):
  phenology_stage                 value = stage letter (C, F, G, H, I1, I2, J1, J2), date of onset/dominance
  repilo_leaf_pct                 % leaves with visible repilo (subtype in `detail`: visible|incubado)
  repilo_plomizo_leaf_pct         % leaves with repilo plomizo
  repilo_plots_pct                % of control plots (ECB) with repilo
  fly_punctured_total_pct         % olives with total sting (picada total)
  fly_punctured_live_pct          % olives with live sting (picada viva)
  fly_punctured_pct               sting % where total/live is not stated
  fly_mcphail_per_trap_day        McPhail captures, flies per trap and day
  fly_chromotropic_per_trap_day   yellow sticky trap captures, flies per plate and day
  fly_trap_per_day                fly trap captures, trap type not stated
  prays_filofaga_shoots_pct       % shoots with live Prays (leaf generation)
  prays_antofaga_infl_pct         % inflorescences attacked with live forms (flower generation)
  prays_carpofaga_fruit_pct       % olives with live Prays (fruit generation)
  prays_adults_per_trap_day       Prays adults per pheromone trap and day

Dates are approximate: the PDFs say "mediados de mayo", "primeros de la segunda decena
de abril", etc. These are mapped to a representative day (see QUALIFIERS) and flagged with
`date_precision` (day | part_of_month | month | none). Values are only taken from the
current campaign (text after "campana pasada/anterior" is cut).

Only stdlib + the `pdftotext` binary (poppler) are used.
"""
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DEFAULT = ROOT / "data/raw/ground_truth/raif"
OUT_DEFAULT = ROOT / "data/processed/ground_truth/raif_olive_labels.csv"

PROVINCES = ["Almería", "Cádiz", "Córdoba", "Granada", "Huelva", "Jaén", "Málaga", "Sevilla"]
MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
          "septiembre", "octubre", "noviembre", "diciembre"]

COLUMNS = ["report_file", "campaign", "level", "province", "zone", "date_iso", "date_text",
           "date_precision", "metric", "value", "unit", "stage_code", "stage_name",
           "qualifier", "detail", "pairing", "context"]


# ---------------------------------------------------------------- text helpers
def strip_acc(s: str) -> str:
    """Remove accents 1:1 (keeps string length so offsets stay valid)."""
    out = []
    for ch in s:
        d = unicodedata.normalize("NFD", ch)
        out.append(d[0] if d else ch)
    return "".join(out)


def low(s: str) -> str:
    return strip_acc(s).lower()


def pdf_text(path: Path) -> str:
    r = subprocess.run(["pdftotext", "-enc", "UTF-8", str(path), "-"],
                       capture_output=True, text=True, check=False)
    return r.stdout


def pdf_text_layout(path: Path) -> str:
    r = subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", str(path), "-"],
                       capture_output=True, text=True, check=False)
    return r.stdout


# Some PDFs were typeset with letter-spacing, giving "r e pilo", "p r incipios".
REPAIR_WORDS = [
    "repilo", "picada", "picadas", "prays", "hojas", "inflorescencias", "inflorescencia", "brotes",
    "aceitunas", "mosquero", "polillero", "viva", "total", "parcelas", "estaciones", "provincial",
    "porcentaje", "principios", "primeros", "mediados", "finales", "decena", "semana", "quincena",
    "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
    "octubre", "noviembre", "diciembre", "visible", "incubado", "plomizo", "floración",
    "endurecimiento", "envero", "cuajado", "media", "valor", "campaña", "pasada", "anterior",
]


def _recase(matched: str, w: str) -> str:
    if not re.search(r"\s", matched):
        return matched
    letters = re.sub(r"\s", "", matched)
    if letters.isupper():
        return w.upper()
    return w.capitalize() if letters[0].isupper() else w


def repair_spacing(text: str) -> str:
    for w in REPAIR_WORDS:
        pat = r"(?<![A-Za-zÁÉÍÓÚÑáéíóúñ])" + r"\s?".join(re.escape(c) for c in w) + r"(?![A-Za-zÁÉÍÓÚÑáéíóúñ])"
        text = re.sub(pat, lambda m, w=w: _recase(m.group(0), w), text, flags=re.IGNORECASE)
    return text


def fix_numbers(text: str) -> str:
    # "0. 8%" / "6, 4 %" -> "0.8%"
    text = re.sub(r"(\d)\s*([.,])\s+(\d{1,2})(?=\s*%)", r"\1\2\3", text)
    text = re.sub(r"(\d)\s+([.,])\s*(\d{1,2})(?=\s*%)", r"\1\2\3", text)
    text = re.sub(r"(\d)\s*[’']\s*(\d)", r"\1.\2", text)  # 14'90 -> 14.90
    text = re.sub(r"(\d)\s+%", r"\1%", text)
    return text


HEADER_KEYS = [
    ("repilo plomizo", "REPILO_PLOMIZO"),
    ("repilo", "REPILO"),
    ("mosca", "MOSCA"),
    ("polilla", "PRAYS"),
    ("prays", "PRAYS"),
]


def classify_header(line: str):
    """Return a section key if `line` is an all-caps heading, else None."""
    s = line.strip()
    if not (4 <= len(s) <= 90):
        return None
    head = s.split("(")[0].strip()
    letters = [c for c in head if c.isalpha()]
    if len(letters) < 4 or sum(c.isupper() for c in letters) / len(letters) < 0.9:
        return None
    if re.search(r"\d{2}", head):
        return None
    h = low(head)
    for k, v in HEADER_KEYS:
        if k in h:
            return v
    if re.search(r"fenolog|general|meteor|climat|aspectos|situacion", h):
        return "GENERAL"
    return "OTHER"


CAPTION_RE = re.compile(r"^[A-ZÁÉÍÓÚÑ][^.;:,]{0,48}$")


def is_caption(line: str) -> bool:
    s = line.strip()
    if not s or re.search(r"[\d%,.;:)]$", s) or re.search(r"\d", s):
        return False
    return bool(CAPTION_RE.match(s)) and len(s.split()) <= 6


def sections(text: str):
    """Yield (section_key, paragraph_text) with captions dropped."""
    cur, buf = "GENERAL", []
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if re.fullmatch(r"\d{1,2}|P\s?á\s?g.*", line):
            continue
        key = classify_header(line) if line else None
        if key:
            if buf:
                out.append((cur, " ".join(buf)))
            buf, cur = [], key
            continue
        if not line:
            continue
        if is_caption(line):
            continue
        buf.append(line)
    if buf:
        out.append((cur, " ".join(buf)))
    return out


def split_sentences(t: str):
    t = re.sub(r"[⮚•●▪►]", ". ", t)
    parts = re.split(r"(?<=[a-záéíóúñ\)%\d])\.\s+(?=[A-ZÁÉÍÓÚÑ“\"])", t)
    out = []
    for p in parts:
        out.extend(x.strip() for x in re.split(r";\s+", p) if x.strip())
    return out


PREV_RE = re.compile(
    r"(pasada\s+(?:campaña|semana)|campaña\s+(?:pasada|anterior)|año\s+(?:pasado|anterior)|"
    r"semana\s+(?:pasada|anterior)|hist[oó]ric|media\s+de\s+la\s+serie|serie\s+hist)", re.IGNORECASE)


def current_part(sentence: str) -> str:
    s = re.sub(r"\([^()]*(?:pasad|anterior|campa|hist[oó]ric|semana|\b20[012]\d\b)[^()]*\)", "", sentence, flags=re.IGNORECASE)
    m = PREV_RE.search(s)
    if m:
        s = s[: m.start()]
        s = re.sub(r"[,;]?\s*(?:mientras que|por otra parte|y|e|siendo|frente a|que)?[,\s]*(?:en|durante)?\s*(?:la|las)?\s*$",
                   "", s, flags=re.IGNORECASE)
    return s


# ---------------------------------------------------------------- dates
QUALIFIERS = [  # (regex on accent-stripped lowercase text before month, representative day, precision)
    (r"primeros? de la segunda decena de$", 12, "part_of_month"),
    (r"primeros? de la tercera decena de$", 22, "part_of_month"),
    (r"finales? de la primera decena de$", 8, "part_of_month"),
    (r"finales? de la segunda decena de$", 18, "part_of_month"),
    (r"finales? de la tercera decena de$", 28, "part_of_month"),
    (r"primera decena de$", 5, "part_of_month"),
    (r"segunda decena de$", 15, "part_of_month"),
    (r"tercera decena de$", 25, "part_of_month"),
    (r"(?:primera|1a) (?:mitad|quincena) de$", 8, "part_of_month"),
    (r"(?:segunda|2a) (?:mitad|quincena) de$", 22, "part_of_month"),
    (r"primera semana de$", 4, "part_of_month"),
    (r"segunda semana de$", 11, "part_of_month"),
    (r"tercera semana de$", 18, "part_of_month"),
    (r"(?:cuarta|ultima) semana de$", 25, "part_of_month"),
    (r"(?:primeros?(?: dias)?|principios|comienzos|inicios?) de$", 5, "part_of_month"),
    (r"mediados de$", 15, "part_of_month"),
    (r"(?:finales|final|fines|fin) de$", 25, "part_of_month"),
]
MONTH_RE = "(" + "|".join(MONTHS) + ")"
EXACT_RE = re.compile(r"(?:semana del |del |el |hasta el )?(\d{1,2}) de " + MONTH_RE)
PART_RE = re.compile(MONTH_RE)


def campaign_years(text: str):
    m = re.search(r"campan?a\s+(\d{4})(?:\s*[-–/]\s*(\d{2,4}))?", strip_acc(text[:4000]), re.IGNORECASE)
    if not m:
        return None, None
    y1 = int(m.group(1))
    y2 = m.group(2)
    if y2:
        y2 = int(y2) if len(y2) == 4 else int(str(y1)[:2] + y2)
    return y1, y2 or y1


def make_iso(year_pair, month: int, day: int):
    y1, y2 = year_pair
    if y1 is None:
        return ""
    year = y1 if (y1 == y2 or month >= 8) else y2
    return f"{year:04d}-{month:02d}-{day:02d}"


def find_dates(sentence: str, year_pair):
    """List of dicts(start, end, text, iso, precision) for date phrases in sentence."""
    ls = low(sentence)
    found, taken = [], []
    for m in EXACT_RE.finditer(ls):
        d, mon = int(m.group(1)), MONTHS.index(m.group(2)) + 1
        if 1 <= d <= 31:
            found.append(dict(start=m.start(), end=m.end(), text=sentence[m.start():m.end()],
                              iso=make_iso(year_pair, mon, d), precision="day"))
            taken.append((m.start(), m.end()))
    for m in PART_RE.finditer(ls):
        if any(a <= m.start() < b for a, b in taken):
            continue
        before = ls[max(0, m.start() - 45): m.start()].rstrip()
        day, prec, qs = 15, "month", m.start()
        for pat, dd, pp in QUALIFIERS:
            mm = re.search(pat.replace("$", r"\s*$"), before)
            if mm:
                day, prec, qs = dd, pp, max(0, m.start() - 45) + mm.start()
                break
        mon = MONTHS.index(m.group(1)) + 1
        found.append(dict(start=qs, end=m.end(), text=sentence[qs:m.end()].strip(),
                          iso=make_iso(year_pair, mon, day), precision=prec))
    found.sort(key=lambda d: d["start"])
    return found


# ---------------------------------------------------------------- entities
def entity_regexes(zone_vocab):
    prov = "|".join(sorted((low(p) for p in PROVINCES), key=len, reverse=True))
    zones = "|".join(re.escape(low(z)) for z in sorted(zone_vocab, key=len, reverse=True)) if zone_vocab else None
    return prov, zones


def find_entities(sentence: str, zone_vocab):
    """Ordered list of (start, end, kind, name, parent_province)."""
    ls = low(sentence)
    prov_alt, zone_alt = entity_regexes(zone_vocab)
    ents = []
    # generic "Zone Name (Province)"
    for m in re.finditer(r"([A-ZÁÉÍÓÚÑ][\wáéíóúñ]+(?:\s+(?:y|de|del|la|el|las)?\s*[A-ZÁÉÍÓÚÑ][\wáéíóúñ]+){0,3})\s*\((" +
                         "|".join(PROVINCES) + r")\)", sentence):
        name = m.group(1)
        if low(name) in {low(p) for p in PROVINCES}:
            continue
        ents.append((m.start(1), m.end(2) + 1, "zone", name.strip(), m.group(2)))
    used = [(e[0], e[1]) for e in ents]
    if zone_alt:
        for m in re.finditer(r"\b(" + zone_alt + r")\b", ls):
            if not any(a <= m.start() < b for a, b in used):
                ents.append((m.start(), m.end(), "zone", sentence[m.start():m.end()].strip(), None))
                used.append((m.start(), m.end()))
    for m in re.finditer(r"\b(" + prov_alt + r")\b", ls):
        if not any(a <= m.start() < b for a, b in used):
            ents.append((m.start(), m.end(), "province", sentence[m.start():m.end()].strip(), None))
    ents.sort()
    return ents


def harvest_zones(layout_text: str):
    """Biological-zone names from the tables / lists each report prints."""
    zones, lines = set(), layout_text.splitlines()
    name = r"[A-Za-zÁÉÍÓÚÑáéíóúñ][A-Za-zÁÉÍÓÚÑáéíóúñ \-/\.]{2,40}?"
    for i, ln in enumerate(lines):
        if re.search(r"ZO\s?NA\s+BIOL[OÓ]GICA", ln, re.IGNORECASE) and re.search(r"ECB|N[ºo°]|ESTACI|Municipios", ln + " " + " ".join(lines[i + 1:i + 3]), re.IGNORECASE):
            for ln2 in lines[i + 1: i + 60]:
                m = re.match(r"^\s*(" + name + r")\s{2,}(\d{1,3})\s*(?:\s{2,}.*)?$", ln2)       # name  N
                m2 = re.match(r"^\s*(" + name + r")\s{3,}[A-ZÁÉÍÓÚÑ][^\d]{2,45}?\s{3,}(\d{1,3})\s*$", ln2)  # name  municipality  N
                for mm in (m, m2):
                    if mm:
                        zones.add(mm.group(1).strip())
    for m in re.finditer(r"^\s*[-•●]?\s*([A-ZÁÉÍÓÚÑ][\wáéíóúñ ]{2,30}?)\s*,\s*compuesta por", layout_text, re.MULTILINE):   # Cadiz
        zones.add(m.group(1).strip())
    for m in re.finditer(r"^\s*([A-ZÁÉÍÓÚÑ][\wáéíóúñ ]{2,30}?):\s*Con\s+[\d.]+\s*has", layout_text, re.MULTILINE):          # Malaga
        zones.add(m.group(1).strip())
    for m in re.finditer(r"(?i:zonas?\s+biol[oó]gicas?\s+(?:de la |del |de las |de )?)([A-ZÁÉÍÓÚÑ][\wáéíóúñ]+(?: (?:de la |del |de )?[A-ZÁÉÍÓÚÑ][\wáéíóúñ]+){0,3})", layout_text):
        cand = m.group(1).strip()
        if " y " not in cand and not re.search(r"^(Olivar|Andaluc|Provincia|Zonas?|Las|Los|El|La)\b", cand):
            zones.add(cand)
    pl = {low(p) for p in PROVINCES}
    bad = r"total|zona|estaci|municipio|olivar|provincia|campa|plaga|mosca|prays|repilo|andalu"
    generic = {"sierra", "campina", "loma", "colonias", "vega", "norte", "sur"}
    return {z for z in zones if low(z) not in pl and low(z) not in generic and len(z) > 3
            and not re.search(bad, low(z)) and not re.search(r"\b(han|ha|con|que|por|las|los|mas|sido|se)\b", low(z))}


# ---------------------------------------------------------------- value extraction
NUM = r"\d{1,3}(?:[.,]\d{1,3})?"
LIST = NUM + r"(?:(?:\s*,\s+|\s+y\s+|\s+e\s+)" + NUM + r")*"
UNIT = (r"(%|(?:adultos|moscas|capturas|machos|polillas)\s*(?:/|por\s+)\s*(?:mosquero|placa|trampa|polillero|trampas)s?)")
GROUP_RE = re.compile(r"(" + LIST + r")\s*" + UNIT, re.IGNORECASE)


def to_float(s: str):
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def expand(listtxt: str):
    return [to_float(x) for x in re.findall(NUM, listtxt)]


def topic_for_pct(after: str, before: str, section: str, sentence: str):
    """Return (metric, detail) or None for a '%' value."""
    a, b = low(after[:90]), low(before[-90:])
    plots = re.match(r"^\s*(?:de\s+)?(?:las|los|el|la)?\s*\d*\s*(?:ecbs?|estaci|parcelas|muestr)", a)
    sl = low(sentence)

    def pick(x):
        # sting
        if re.search(r"picad|aceitunas? con (?:mosca|picada)|fruto afectado", x):
            if re.search(r"viv[ao]|vida", x):
                return "fly_punctured_live_pct"
            if "total" in x:
                return "fly_punctured_total_pct"
            return "fly_punctured_pct"
        if section == "REPILO_PLOMIZO" or "plomizo" in x:
            return "repilo_plomizo_leaf_pct" if "hoja" in x or section == "REPILO_PLOMIZO" else None
        if re.search(r"hojas?", x) and (section.startswith("REPILO") or "repilo" in sl):
            return "repilo_leaf_pct"
        if section == "PRAYS" or "prays" in sl:
            if re.search(r"flores|por brote|fertil", x):
                return None
            if re.search(r"brotes", x):
                return "prays_filofaga_shoots_pct"
            if "inflorescencia" in x:
                return "prays_antofaga_infl_pct"
            if re.search(r"aceituna|fruto", x):
                return "prays_carpofaga_fruit_pct"
        return None

    metric = pick(a) or pick(b)
    if metric is None:
        return None
    detail = ""
    if metric == "repilo_leaf_pct":
        detail = "incubado" if re.search(r"incubad", a + b) else "visible"
    if plots:
        base = metric.replace("_leaf_pct", "").replace("_pct", "")
        return (f"{base.split('_')[0]}_plots_pct" if metric.startswith("repilo") else metric.replace("_pct", "_plots_pct")), detail
    return metric, detail


def topic_for_trap(unit: str, section: str, sentence: str):
    u = low(unit)
    if "mosquero" in u:
        return "fly_mcphail_per_trap_day"
    if "placa" in u:
        return "fly_chromotropic_per_trap_day"
    if "polillero" in u:
        return "prays_adults_per_trap_day"
    if "trampa" in u:
        if section == "PRAYS" or "prays" in low(sentence):
            return "prays_adults_per_trap_day"
        if section == "MOSCA" or "mosca" in low(sentence):
            return "fly_trap_per_day"
    return None


def extract_values(sentence: str, section: str, report_province: str, zone_vocab, year_pair, inherit_date, campaign):
    s = current_part(fix_numbers(sentence))
    s = re.sub(r"pasando\s+del?\s+[\d.,]+\s*%?\s+al?\s+([\d.,]+)", r"con \1", s, flags=re.IGNORECASE)
    rows = []
    if not s.strip():
        return rows
    ents = find_entities(s, zone_vocab)
    dates = find_dates(s, year_pair)
    used = set()
    groups = list(GROUP_RE.finditer(s))
    for gi, g in enumerate(groups):
        vals = [v for v in expand(g.group(1)) if v is not None]
        unit = g.group(2)
        nxt = groups[gi + 1].start() if gi + 1 < len(groups) else len(s)
        after = s[g.end(): nxt]
        before = s[: g.start()]
        if unit == "%":
            topic = topic_for_pct(after, before, section, s)
            unit_name = "%"
        else:
            m = topic_for_trap(unit, section, s)
            topic = (m, "") if m else None
            unit_name = "per_trap_day"
        if topic is None:
            continue
        metric, detail = topic
        if section == "OTHER":
            continue
        qual = "max" if re.search(r"m[aá]xim", low(before[-80:] + after[:40])) else "mean_or_unspecified"
        if re.search(r"(?:inferior(?:es)?|menos|menor(?:es)?|por debajo)\s+(?:de|a)\s*(?:los\s+)?$", low(before[-25:])):
            qual = "upper_bound"
        elif re.search(r"(?:superior(?:es)?|mas|mayor(?:es)?|por encima)\s+(?:de|a)\s*(?:los\s+)?$", low(before[-25:])):
            qual = "lower_bound"
        # entity pairing: nearest n unused entities preceding the group
        pre = [e for e in ents if e[1] <= g.start() + 1 and e[0] not in used]
        chosen, pairing = [], "provincial"
        if len(vals) > 1 and len(pre) >= len(vals):
            chosen, pairing = pre[-len(vals):], "list"
        elif len(vals) == 1 and pre:
            chosen, pairing = [pre[-1]], "nearest"
        elif len(vals) > 1:
            chosen, pairing = [None] * len(vals), "unresolved_entity"
        else:
            chosen = [None]
        for e in chosen:
            if e is not None:
                used.add(e[0])
        # date: nearest date phrase to the group, else inherited
        d = None
        if dates:
            prev = [x for x in dates if x["start"] < g.start()]
            d = max(prev, key=lambda x: x["start"]) if prev else min(dates, key=lambda x: x["start"])
        elif inherit_date and not re.search(r"a lo largo de|toda la campa|final de (?:la )?campa|durante la campa|final de su seguimiento|al final", low(s)):
            d = dict(inherit_date, text=inherit_date["text"] + " (prev. sentence)", precision="inherited")
        for v, e in zip(vals, chosen):
            if e is None:
                level = "region" if report_province == "Andalucía" else "province"
                if pairing == "unresolved_entity":
                    level = "unresolved"
                prov, zone = report_province, ""
            elif e[2] == "province":
                level = "province"
                prov, zone = e[3], ""
            else:
                level = "zone"
                prov, zone = (e[4] or report_province), e[3]
            rows.append(dict(
                level=level, province=prov, zone=zone, metric=metric, value=v, unit=unit_name,
                date_iso=d["iso"] if d else "", date_text=d["text"] if d else "",
                date_precision=d["precision"] if d else "none", qualifier=qual,
                detail=detail, pairing=pairing, stage_code="", stage_name="",
                context=re.sub(r"\s+", " ", sentence)[:260]))
    return rows


# ---------------------------------------------------------------- phenology
STAGES = [  # (regex on accent-stripped lowercase, code, name)
    (r"envero[ -]*(?:/|-)?\s*amarill|\bi\s?1\b", "I1", "envero amarilleo"),
    (r"envero[ -]*(?:-|,)?\s*manchas|manchas rojas|\bi\s?2\b", "I2", "envero manchas rojas"),
    (r"pulpa blanca|\bj\s?1\b", "J1", "fruto maduro pulpa blanca"),
    (r"pulpa roja|\bj\s?2\b", "J2", "fruto maduro pulpa roja"),
    (r"endurecimiento|hueso endurecid", "H", "endurecimiento de hueso"),
    (r"cuajad", "G", "fruto cuajado"),
    (r"floracion|primeras flores|plena flor|apertura de (?:las )?flores", "F", "floracion"),
    (r"formacion (?:del racimo|de (?:las )?inflorescencia)|primeras inflorescencias|estado .?c.? ", "C", "formacion inflorescencias"),
    (r"envero", "I", "envero"),
]
STAGE_LETTER = re.compile(r"estados? (?:fenol[oó]gicos? )?(?:dominante )?[“\"”]\s?([A-J][12]?)\s?[”\"“]")


def phenology_rows(sentence, section, report_province, zone_vocab, year_pair):
    if section not in ("GENERAL",):
        return []
    s = current_part(sentence)
    ls = low(s)
    if not re.search(r"fenol|estado|inflorescencia|floracion|flores|envero|hueso|cuajad|fruto", ls):
        return []
    dates = find_dates(s, year_pair)
    if not dates:
        return []
    code = name = None
    best = None
    m = STAGE_LETTER.search(s)
    if m:
        code = m.group(1).replace(" ", "")
        name = {"C": "formacion inflorescencias", "D": "despliegue corola", "F": "floracion",
                "H": "endurecimiento de hueso", "I1": "envero amarilleo", "I2": "envero manchas rojas",
                "J1": "fruto maduro pulpa blanca", "J2": "fruto maduro pulpa roja"}.get(code, "")
        best = m.start()
    for pat, c, n in STAGES:
        mm = re.search(pat, ls)
        if mm and (best is None or mm.start() < best):
            code, name, best = c, n, mm.start()
            break
    if code is None:
        return []
    cut = re.search(r"a excepcion de|excepto|salvo", ls)
    ents = find_entities(s[: cut.start()] if cut else s, zone_vocab)
    rel = bool(re.search(r"siguiente|posterior|seguid|a continuacion|semanas? despu", ls))
    rows = []

    def row(e, d, pairing):
        if e is None:
            level, prov, zone = ("region" if report_province == "Andalucía" else "province"), report_province, ""
        elif e[2] == "province":
            level, prov, zone = "province", e[3], ""
        else:
            level, prov, zone = "zone", (e[4] or report_province), e[3]
        rows.append(dict(level=level, province=prov, zone=zone, metric="phenology_stage", value=code,
                         unit="stage", date_iso=d["iso"], date_text=d["text"],
                         date_precision=d["precision"], qualifier="onset_or_dominant",
                         detail=name, pairing=pairing + ("+relative_dates" if rel else ""),
                         stage_code=code, stage_name=name,
                         context=re.sub(r"\s+", " ", sentence)[:260]))

    if not ents:
        for d in dates[:1]:
            row(None, d, "provincial")
    else:
        for e in ents:
            d = min(dates, key=lambda x: (min(abs(x["start"] - e[0]), abs(x["end"] - e[1])), x["start"] > e[0]))
            row(e, d, "nearest_date")
    return rows


# ---------------------------------------------------------------- report driver
def report_province(head: str):
    """Province from the cover ("PROVINCIA DE X" or the capitalised title), else Andalucía (autonomic)."""
    head = head[:500]
    m = re.search(r"PROVINCIA\s+DE\s+([A-ZÁÉÍÓÚÑ]+)", head)
    cand = m.group(1) if m else None
    if cand is None:
        for p in PROVINCES:
            if re.search(r"\b" + p.upper() + r"\b", head):
                cand = p
                break
    if cand:
        for p in PROVINCES:
            if low(p) == low(cand):
                return p
    return "Andalucía"


def process(pdf: Path, years):
    raw = pdf_text(pdf)
    text = fix_numbers(repair_spacing(raw))
    y1, y2 = campaign_years(text)
    if y1 is None or not (years[0] <= y1 <= years[1]):
        return None, f"skipped (campaign {y1})"
    province = report_province(text[:1500])
    zone_vocab = harvest_zones(pdf_text_layout(pdf))
    rows, prev_date = [], None
    for section, para in sections(text):
        prev_date = None
        for sent in split_sentences(para):
            ph = phenology_rows(sent, section, province, zone_vocab, (y1, y2))
            vals = extract_values(sent, section, province, zone_vocab, (y1, y2), prev_date, y1)
            dd = find_dates(current_part(sent), (y1, y2))
            if dd:
                prev_date = dd[-1]
            for r in ph + vals:
                r["report_file"] = pdf.name
                r["campaign"] = f"{y1}-{y2}" if y1 != y2 else str(y1)
                rows.append(r)
    return rows, f"{province}, campaign {y1 if y1 == y2 else f"{y1}-{y2}"}, zones={len(zone_vocab)}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", type=Path, default=RAW_DEFAULT)
    ap.add_argument("--out", type=Path, default=OUT_DEFAULT)
    ap.add_argument("--years", default="2022-2025", help="campaign start-year range to keep")
    a = ap.parse_args()
    lo, hi = (int(x) for x in a.years.split("-"))
    allrows, seen = [], set()
    for pdf in sorted(a.raw.glob("*.pdf")):
        rows, info = process(pdf, (lo, hi))
        if rows is None:
            print(f"  {pdf.name}: {info}", file=sys.stderr)
            continue
        n_new = 0
        for r in rows:
            key = (r["province"], r["zone"], r["metric"], r["value"], r["date_iso"], r["campaign"], r["detail"], r["context"][:80])
            if key in seen:  # same report published twice under different file names
                continue
            seen.add(key)
            allrows.append(r)
            n_new += 1
        print(f"  {pdf.name}: {info}: {n_new} rows", file=sys.stderr)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(allrows)
    from collections import Counter
    c = Counter(r["metric"] for r in allrows)
    print(f"\nWrote {len(allrows)} rows -> {a.out}")
    for k, v in sorted(c.items()):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
