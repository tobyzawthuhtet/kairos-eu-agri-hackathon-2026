.PHONY: install test lint api web
install:
	uv sync
	cd web && npm install
test:
	uv run pytest
lint:
	uv run ruff check .
api:
	uv run uvicorn kairos.api.main:app --reload
web:
	cd web && npm run dev

backtest:
	uv run python scripts/backtest_raif.py

demo:
	uv run python scripts/build_demo_html.py

demo-up:
	uv run python scripts/demo_up.py

demo-down:
	-@for p in 8000 8501 5050; do lsof -ti tcp:$$p -sTCP:LISTEN | xargs -r kill 2>/dev/null; done; ollama stop $${KAIROS_LLM:-qwen2.5:3b} >/dev/null 2>&1; echo "demo stopped (model unloaded)"
