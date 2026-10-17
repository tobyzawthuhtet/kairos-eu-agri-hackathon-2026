"""Grounded Q&A: retrieve rules, give the model only that context, check the answer, fall back to the template."""
import re

from kairos.assist import corpus, feedback, llm
from kairos.assist.retrieve import retrieve
from kairos.rules import reviews

SYSTEM = """You are Elena's assistant on a farm weather-alert app for olive growers.
Answer ONLY from the CONTEXT. Use short, plain sentences (at most 5) in the language of the question.
Never invent numbers, thresholds, products or doses. If the context does not answer, say: "I don't have a validated rule for that. Ask your advisor."
Reply entirely in the language of the question, including the refusal sentence. Do not repeat the labels 'Lead time', 'Confidence' or 'Validated'.
Mention the rule id you used in brackets, like [OLV-S01-FROST-01]. You explain alerts; you never create, cancel or change them."""

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
    docs = retrieve(question, k=3, crop=crop, must_include=[rule["id"]] if rule.get("id") else None)
    haz = (alert or {}).get("hazard")
    shots = [f"Q: {e['question']}\nA: {e['answer']}" for e in feedback.examples(haz)]
    ctx = "\n".join(["CONTEXT:", alert_context(alert), *[f"- {d['text']}" for d in docs],
                     *(["ADVISOR-APPROVED EXAMPLES (style and substance):", *shots] if shots else [])])
    fallback = (alert["advice"]["headline"] + " " + " ".join(alert["advice"]["steps"])) if alert else \
        "I don't have a validated rule for that. Ask your advisor."
    cites = [{"rule_id": d["id"], "source_url": d["source_url"]} for d in docs]
    out = {"id": None, "citations": cites, "model": llm.MODEL, "grounded": False}
    text = llm.chat(SYSTEM, f"{ctx}\n\nQUESTION: {question}") if llm.available() else None
    if text is None:
        return {**out, "text": fallback, "backend": "template", "note": "Language model not available; showing the standard advice."}
    bad = verify(text, ctx)
    if bad:
        return {**out, "text": fallback, "backend": "template", "rejected": text, "unsupported_numbers": bad,
                "note": "Model answer contained numbers not in the rules; showing the standard advice."}
    return {**out, "text": text, "backend": "ollama", "grounded": True}


EXPLAIN_SYSTEM = """You help an agronomist check why a weather-alert system fired. Write exactly 3 bullets, each ONE sentence of at most 25 words, in English, using only the CONTEXT:
1. Why it fired: the reading against the rule's trigger and the crop stage.
2. What the rule is based on: the evidence or source named in the context.
3. What to double-check before validating: limits such as unvalidated threshold, estimated stage, reanalysis data, or low confidence.
Never invent numbers or sources. Cite the rule id in brackets. Do not suggest changing thresholds."""


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
    fallback = "\n".join(f"- {f}" for f in facts(alert)) + f"\n- Source: {alert['source']}"
    out = {"citations": [{"rule_id": d["id"], "source_url": d["source_url"]} for d in docs], "facts": facts(alert), "model": llm.MODEL, "grounded": False}
    text = llm.chat(EXPLAIN_SYSTEM, ctx) if llm.available() else None
    bad = verify(text, ctx) if text else []
    if text is None or bad:
        res = {**out, "text": fallback, "backend": "template", "note": "Language model not available; showing the facts only." if text is None
               else "Model explanation had numbers not in the rules; showing the facts only."}
    else:
        res = {**out, "text": text, "backend": "ollama", "grounded": True}
    res["id"] = feedback.log_answer("Why did the system trigger this?", res, alert["id"], alert.get("hazard"))
    return res
