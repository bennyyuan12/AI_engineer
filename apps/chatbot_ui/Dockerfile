FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY apps/chatbot_ui ./apps/chatbot_ui

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package chatbot-ui

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/app/.venv/bin:$PATH"
ENV HOME=/home/app

RUN addgroup --system app && \
    adduser --system --ingroup app --home /home/app app && \
    chown -R app:app /app

USER app

EXPOSE 8501

WORKDIR /app/apps/chatbot_ui/src

CMD ["streamlit", "run", "chatbot_ui/app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
