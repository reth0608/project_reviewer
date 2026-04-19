FROM python:3.11-slim

RUN useradd -m -u 1000 sandbox
WORKDIR /app
RUN chown sandbox:sandbox /app

RUN pip install --no-cache-dir pytest pytest-timeout

USER sandbox
CMD ["pytest", "--tb=short", "--timeout=20", "-v"]
