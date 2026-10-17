"""Grounded Q&A: retrieve rules, give the model only that context, check the answer, fall back to the template."""
import re

from kairos.assist import corpus, feedback, llm
from kairos.assist.retrieve import retrieve
from kairos.rules import reviews

SYSTEM = """You explain farm weather alerts to an olive grower, in plain everyday words.
Answer ONLY from the CONTEXT, in at most 3 short sentences, in the language of the question. Say what is happening, and why it matters for the trees.
Do not give orders or doses: the app already shows the advice. No rule ids, no jargon such as 'trigger', 'threshold' or 'rule'.
Never invent numbers, products or sources. If the context does not answer, say: "I don't have a validated answer for that. Ask your advisor." (in the language of the question)."""

NUM = re.compile(r"\d+(?:[.,]\d+)?")


def _numbers(text: str) -> set[str]:
    return {n.replace(",", ".").rstrip("0").rstrip(".") if "." in n.replace(",", ".") else n for n in NUM.findall(text)}


def verify(answer: str, context: str) -> list[str]:
    """Numbers in the answer that are not in the context (rule ids are ignored)."""
    body = re.sub(r"(?m)^\s*\d+[.)]\s+", "", re.sub(r"\[[^\]]*\]", "", answer))  # drop rule ids and list numbering
    return sorted(_numbers(body) - _numbers(context))


def alert_context(alert: dict | None) -> str:
    if not alert:
        return ""
    r = alert.get("rule") or {}
    ev = " ".join(e["text"] for e in alert.get("evidence", []))
    return (f"TODAY'S ALERT: {alert['title']}. {alert['summary']} Severity {alert['severity_ui']}. Rule {r.get('id')}: value {r.get('value')} "
            f"{r.get('operator')} {r.get('threshold')} {r.get('unit')}. Advice: {alert['advice']['headline']} {' '.join(alert['advice']['steps'])} {ev}")


def answer(question: str, alert: dict | None = None, crop: str = "olive") -> dict:
    res = _answer(question, alert, crop)
    res["id"] = feedback.log_answer(question, res, (alert or {}).get("id"), (alert or {}).get("hazard"))
    return res


def _answer(question: str, alert: dict | None, crop: str) -> dict:
    rule = (alert or {}).get("rule") or {}
    if alert:
        # Answering about a specific alert: use the fired rule only. Neighbouring rules led the model (and the citations) astray.
        docs = [d for d in corpus.documents(crop) if d["id"] == rule.get("id")]
    else:
        docs = retrieve(question, k=3, crop=crop)
    haz = (alert or {}).get("hazard")
    shots = [f"Q: {e['question']}\nA: {e['answer']}" for e in feedback.examples(haz)]
    ctx = "\n".join(["CONTEXT:", alert_context(alert), *[f"- {d['text']}" for d in docs],
                     *(["ADVISOR-APPROVED EXAMPLES (style and substance):", *shots] if shots else [])])
    fallback = plain_fallback(alert) if alert else "I don't have a validated answer for that. Ask your advisor."
    cites = [{"rule_id": d["id"], "source_url": d["source_url"]} for d in docs]
    out = {"id": None, "citations": cites, "model": llm.MODEL, "grounded": False}
    text = llm.chat(SYSTEM, f"{ctx}\n\nQUESTION: {question}") if llm.available() else None
    text = tidy(text) if text else text
    if text is None:
        return {**out, "text": fallback, "backend": "template", "note": "Language model not available; showing a plain summary."}
    bad = verify(text, ctx)
    if bad:
        return {**out, "text": fallback, "backend": "template", "rejected": text, "unsupported_numbers": bad,
                "note": "Model answer contained numbers not in the rules; showing a plain summary."}
    return {**out, "text": text, "backend": "ollama", "grounded": True}


EXPLAIN_SYSTEM = """You explain to an agronomist, in plain everyday words, what is happening in the field that made a weather alert appear.
Write 2 or 3 short sentences using only the CONTEXT: what the weather did, what stage the trees are in, and why that matters.
Do not restate the advice or the decision. No rule ids and no jargon such as 'trigger', 'threshold' or 'rule'. Never invent numbers or sources.
If something is uncertain (estimated stage, unvalidated, low confidence), add one short sentence saying so."""


def tidy(text: str) -> str:
    """Remove rule ids and list markers the model may still add, so the reader gets plain prose."""
    text = re.sub(r"\s*\[[A-Z0-9-]+\]", "", text)
    return re.sub(r"(?m)^\s*(?:[-*]|\d+[.)])\s+", "", text).strip()


def plain_fallback(alert: dict) -> str:
    """No model: say what happened in the farmer's words, from the alert's own summary and stage line."""
    stage = next((e["text"] for e in alert.get("evidence", []) if e["text"].startswith("Crop stage")), "")
    return " ".join(x for x in (alert["summary"], stage) if x)


def facts(alert: dict) -> list[str]:
    """Deterministic checks shown next to the model's explanation, so the advisor never depends on the LLM for the numbers."""
    r = alert.get("rule") or {}
    out = []
    if r:
        out.append(f"Reading {r.get('value')} {r.get('operator')} trigger {r.get('threshold')} {r.get('unit') or ''}".strip())
        out.append("Threshold validated by an agronomist" if r.get("validated") else "Threshold not yet validated by an agronomist")
    out.append(f"Advice confidence: {alert['advice'].get('confidence')}")
    if alert.get("demo_data"):
        out.append("Demo rule or data: needs calibration")
    return out


_CACHE: dict[tuple, dict] = {}


def explain(alert: dict, crop: str = "olive") -> dict:
    """Cached per alert and reading: the same alert opened again (or by another advisor) is instant."""
    key = (alert["id"], (alert.get("rule") or {}).get("value"), reviews.mtime())
    hit = key in _CACHE
    if not hit:
        _CACHE[key] = _explain(alert, crop)
    return {**_CACHE[key], "cached": hit}


def _explain(alert: dict, crop: str) -> dict:
    rule = alert.get("rule") or {}
    # Only the rule that fired: pulling neighbours in made the small model blend unrelated rules into the rationale.
    # Kairos demo rules (soil drying etc.) have no table row, so their context is the alert itself.
    docs = [d for d in corpus.documents(crop) if d["id"] == rule.get("id")]
    ctx = "\n".join(["CONTEXT:", alert_context(alert), *[f"- {d['text']}" for d in docs]])
    fallback = plain_fallback(alert)
    out = {"citations": [{"rule_id": d["id"], "source_url": d["source_url"]} for d in docs], "facts": facts(alert), "model": llm.MODEL, "grounded": False}
    text = llm.chat(EXPLAIN_SYSTEM, ctx) if llm.available() else None
    text = tidy(text) if text else text
    bad = verify(text, ctx) if text else []
    if text is None or bad:
        res = {**out, "text": fallback, "backend": "template", "note": "Language model not available; showing a plain summary." if text is None
               else "Model explanation had numbers not in the rules; showing a plain summary."}
    else:
        res = {**out, "text": text, "backend": "ollama", "grounded": True}
    res["id"] = feedback.log_answer("Why did the system trigger this?", res, alert["id"], alert.get("hazard"))
    return res
