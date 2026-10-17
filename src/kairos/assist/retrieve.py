"""Structured filter, then BM25 ranking (optionally blended with Ollama embeddings)."""
import math
import re
from collections import Counter

from kairos.assist import corpus

_tok = lambda s: re.findall(r"[a-z0-9áéíóúñ]+", s.lower())

STOP = {"the", "a", "an", "of", "and", "or", "to", "in", "on", "is", "are", "for", "with", "what", "why", "how", "do", "does", "my", "this", "that", "it", "be", "at", "from", "by", "as"}


def _bm25(query: list[str], docs: list[list[str]], k1=1.4, b=0.75) -> list[float]:
    n, avg = len(docs), sum(map(len, docs)) / max(len(docs), 1)
    df = Counter(t for d in docs for t in set(d))
    out = []
    for d in docs:
        tf, s = Counter(d), 0.0
        for t in query:
            if t in tf:
                idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
                s += idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * len(d) / avg))
        out.append(s)
    return out


HAZARD_WORDS = {"fly": ("fly", "mosca"), "repilo": ("peacock", "repilo"), "hail": ("hail", "granizo"), "wind": ("wind", "gust", "viento"),
                "frost": ("frost", "freez", "cold", "helada"), "heat": ("heat", "hot", "calor"),
                "drought": ("drought", "dry", "sequ", "water", "irrigat", "riego")}  # specific pests first: "how hot for the fly" is a fly question


def guess_hazard(question: str, docs: list[dict]) -> str | None:
    """Map a free-text question to a hazard family; returns a hazard id only if it exists in the table."""
    q = question.lower()
    for fam, words in HAZARD_WORDS.items():
        if any(w in q for w in words):
            hits = [d["hazard"] for d in docs if fam in d["hazard"] or d["hazard"] in fam]
            if hits:
                return Counter(hits).most_common(1)[0][0] if not any(d["hazard"] == fam for d in docs) else fam
    return None


def retrieve(question: str, k: int = 4, crop: str = "olive", hazard: str | None = None, stage: str | None = None,
             must_include: list[str] | None = None) -> list[dict]:
    """Hard filters (hazard/stage) are exact; BM25 only orders what survives. Rules named in must_include come first."""
    docs = corpus.documents(crop)
    hazard = hazard or (guess_hazard(question, docs) if not must_include else None)
    pool = [d for d in docs if (not hazard or d["hazard"] == hazard) and (not stage or stage in d["stage"].split("|"))]
    if hazard and len(pool) < 2:
        pool = [d for d in docs if d["hazard"] == hazard] or docs
    q = [t for t in _tok(question) if t not in STOP]
    scores = _bm25(q, [_tok(d["text"]) for d in pool])
    ranked = [d for _, d in sorted(zip(scores, pool, strict=True), key=lambda x: -x[0])]
    first = [d for d in docs if d["id"] in (must_include or [])]
    out = first + [d for d in ranked if d not in first]
    return out[:k]
