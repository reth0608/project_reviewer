FROM python:3.11-slim AS builder

WORKDIR /build
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir build && \
    pip install --no-cache-dir \
        fastapi uvicorn PyGithub pygit2 \
        "langgraph>=0.1.0" "langchain-google-genai>=2.0.0" langsmith \
        python-dotenv pydantic httpx "pyjwt[crypto]" \
        tree-sitter tree-sitter-python docker ruff mypy

FROM python:3.11-slim AS runtime

RUN useradd -m -u 1000 agent
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY agent/ ./agent/
COPY sandbox/ ./sandbox/

EXPOSE 8000
USER agent
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "agent.webhook_server:app", "--host", "0.0.0.0", "--port", "8000"]
