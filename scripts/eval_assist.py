"""Small faithfulness check for the RAG assistant. Run with Ollama up: uv run python scripts/eval_assist.py"""
import time

from kairos.assist import ask, llm
from kairos.assist.retrieve import retrieve

# (question, hazard family the retrieved rules must belong to)
GOLDEN = [
    ("What should I do after a frost on my olive trees?", "frost"),
    ("¿Qué hago si hay helada durante la floración?", "frost"),
    ("When is peacock spot a risk?", "peacock"),
    ("How hot is too hot for the olive fly?", "fly"),
    ("What do I do if hail hits the grove?", "hail"),
    ("Strong gusts are forecast, what should I check?", "wind"),
    ("How should I irrigate in a water deficit?", "deficit"),
    ("What is the best fertiliser brand?", None),  # not in the rules: should refuse
]


def main() -> None:
    print(f"model={llm.MODEL} available={llm.available()}")
    ok = grounded = 0
    for q, fam in GOLDEN:
        docs = retrieve(q, k=3)
        hit = fam is None or any(fam in d["hazard"] for d in docs)
        t = time.time()
        r = ask.answer(q)
        ok += hit
        grounded += r["grounded"]
        print(f"\nQ: {q}\n  retrieval {'OK' if hit else 'MISS'} {[d['id'] for d in docs]}\n  {r['backend']} grounded={r['grounded']} {time.time() - t:.1f}s"
              f"{' unsupported=' + str(r.get('unsupported_numbers')) if r.get('unsupported_numbers') else ''}\n  A: {r['text']}")
    print(f"\nretrieval {ok}/{len(GOLDEN)}  grounded answers {grounded}/{len(GOLDEN)}")


if __name__ == "__main__":
    main()
