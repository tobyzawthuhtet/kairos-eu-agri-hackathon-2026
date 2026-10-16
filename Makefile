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
