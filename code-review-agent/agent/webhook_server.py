import asyncio
import hashlib
import hmac
import json
import logging
import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Code Review Agent")
WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET", "").encode()


def verify_signature(payload_bytes: bytes, signature_header: str | None) -> bool:
    if not WEBHOOK_SECRET or not signature_header:
        return False
    try:
        algo, sig = signature_header.split("=", 1)
    except ValueError:
        return False
    if algo != "sha256":
        return False
    expected = hmac.new(WEBHOOK_SECRET, payload_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhook")
async def handle_webhook(request: Request) -> JSONResponse:
    body = await request.body()
    sig = request.headers.get("X-Hub-Signature-256")

    if not verify_signature(body, sig):
        logger.warning("Invalid webhook signature rejected")
        raise HTTPException(status_code=401, detail="Invalid signature")

    event = request.headers.get("X-GitHub-Event", "unknown")
    payload = json.loads(body)
    action = payload.get("action", "unknown")

    logger.info("Event: %s | Action: %s", event, action)

    if event == "pull_request" and action in ("opened", "synchronize", "reopened"):
        repo_name = payload["repository"]["full_name"]
        pr_number = payload["pull_request"]["number"]
        logger.info("PR #%s in %s queued for review", pr_number, repo_name)

        from agent.pipeline import run_agent_on_pr

        asyncio.create_task(run_agent_on_pr(repo_name, pr_number))

    return JSONResponse({"status": "accepted"})


if __name__ == "__main__":
    uvicorn.run("agent.webhook_server:app", host="0.0.0.0", port=8000, reload=True)
