# LLM-powered code review agent

An autonomous agent that reviews GitHub Pull Requests, generates verified fixes
using sandboxed execution, and posts structured review comments.

## What makes this not a wrapper

1. **Execution grounding** - every suggested fix is applied and run inside a
   Docker sandbox before being posted. The LLM generates hypotheses; the
   sandbox verifies them.
2. **Agentic loop** - plan -> generate -> execute -> evaluate -> retry
   (up to 3x), implemented as a LangGraph state machine.
3. **AST-level analysis** - changed files are parsed with tree-sitter, not fed
   as raw diffs. The agent receives structured function metadata.
4. **Measured** - evaluated on a 10-entry golden dataset with pass@1, pass@3,
   hallucination rate, LLM-as-judge score, and semantic scope violation rate.

## Eval results (baseline)

| Metric | Score |
|---|---|
| pass@1 | pending |
| pass@3 | pending |
| hallucination rate | pending |
| LLM judge score | pending |
| scope violation rate | pending |

## Architecture

Paste the LangGraph graph image here after running `python scripts/export_graph.py`.

## Run locally

### Prerequisites

- Python 3.11 recommended
- Docker Desktop running
- A GitHub App configured for pull request webhooks
- A Gemini API key
- A LangSmith API key

### 1. Enter the project directory

```powershell
cd D:\Coding\code_reviewer\code-review-agent
```

### 2. Create and fill your environment file

Copy `.env.example` to `.env` and fill in:

```env
GITHUB_APP_ID=...
GITHUB_APP_PRIVATE_KEY_PATH=./secrets/github_private_key.pem
GITHUB_WEBHOOK_SECRET=...
GITHUB_TEST_REPO=yourname/your-test-repo
GEMINI_API_KEY=...
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=code-review-agent
DEPLOY_URL=
```

Place your GitHub App PEM file at `secrets/github_private_key.pem`.

### 3. Install dependencies

Try the editable install first:

```powershell
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e . --no-build-isolation
python -m pip install pytest pytest-asyncio ruff mypy
```

If that still resolves slowly, install the direct dependencies instead:

```powershell
python -m pip install fastapi "uvicorn[standard]" PyGithub pygit2 docker langgraph langchain-google-genai langsmith python-dotenv pydantic httpx "pyjwt[crypto]" tree-sitter tree-sitter-python pytest pytest-asyncio ruff mypy
```

### 4. Build the sandbox image

```powershell
docker build -t code-review-sandbox:latest .\sandbox\
```

### 5. Run quick local checks

```powershell
python -m pytest tests -q
python -m ruff check agent sandbox evals tests scripts --no-cache
```

### 6. Test the analysis pipeline manually

Replace the repo and PR number with a real PR you can access through the GitHub App:

```powershell
python .\scripts\test_analysis.py yourname/your-test-repo 1
```

### 7. Start the webhook server

```powershell
python -m agent.webhook_server
```

The health endpoint is available at `http://localhost:8000/health`.

### 8. Expose the webhook publicly

Use ngrok or a similar tunnel:

```powershell
ngrok http 8000
```

Then set your GitHub App webhook URL to:

```text
https://your-ngrok-url/webhook
```

### 9. Trigger a review

Open or update a pull request in `GITHUB_TEST_REPO`. The server should log the webhook event, run the agent loop, and post a PR comment when GitHub auth, Gemini, LangSmith, and Docker are all configured correctly.

### 10. Optional local eval run

This uses the LLM and sandbox, so it requires a working Gemini key and Docker image:

```powershell
python .\evals\run_evals.py
```

## Live demo

Add your demo video link here after recording it.

## Known limitations

- Only handles Python files today.
- Requires at least one test file to exist; otherwise it falls back to a placeholder test.
- Multi-file refactors are not supported in a single auto-fix loop.
- The sandbox has a short execution timeout and will fail very slow test suites.
- The GitHub App must be installed on each repository you want to review.
