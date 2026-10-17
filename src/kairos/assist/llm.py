"""Thin Ollama client. Never raises: callers fall back to the template text."""
import os

import httpx

HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODEL = os.environ.get("KAIROS_LLM", "qwen2.5:3b")


def available() -> bool:
    try:
        tags = httpx.get(f"{HOST}/api/tags", timeout=1.5).json().get("models", [])
        return any(m["name"].split(":")[0] == MODEL.split(":")[0] for m in tags)
    except (httpx.HTTPError, ValueError, KeyError):
        return False


def chat(system: str, user: str, timeout: float = 90.0) -> str | None:
    try:
        r = httpx.post(f"{HOST}/api/chat", timeout=timeout, json={
            "model": MODEL, "stream": False, "keep_alive": "30m",
            "options": {"temperature": 0.1, "num_predict": 220, "num_ctx": 4096},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
        r.raise_for_status()
        return r.json()["message"]["content"].strip()
    except (httpx.HTTPError, ValueError, KeyError):
        return None


def warm() -> None:
    """Load the model into memory so the first real question is not the slow one."""
    if available():
        chat("Reply with OK.", "OK", timeout=60)


def unload() -> None:
    """Free the model's memory now (keep_alive 0). The Ollama daemon itself stays up; it is idle and may belong to the Ollama app."""
    try:
        httpx.post(f"{HOST}/api/generate", json={"model": MODEL, "keep_alive": 0}, timeout=5)
    except httpx.HTTPError:
        pass
