FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
COPY configs ./configs
RUN uv sync --no-dev
ENV KAIROS_CONFIG_DIR=/app/configs
CMD ["uv", "run", "uvicorn", "kairos.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
