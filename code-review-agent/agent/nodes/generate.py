import json
import logging

from agent.llm import get_llm
from agent.state import AgentState

logger = logging.getLogger(__name__)

GENERATE_PROMPT = """You are a senior Python engineer. Generate a minimal fix for
the following code issue.

ISSUE:
{issue}

ORIGINAL FILE CONTENT ({filename}):
```python
{file_content}
```

Rules:
- Output ONLY a unified diff patch in JSON.
- The patch must be minimal and touch only lines related to the issue.
- Do not reformat or rename unrelated code.
- Include enough context lines for the patch to apply cleanly.

Respond ONLY with valid JSON:
{{
  "patch": "<unified diff starting with --- and +++>",
  "explanation": "One sentence explaining the change."
}}"""


def generate_node(state: AgentState) -> dict:
    issue = json.loads(state["current_issue"])
    analysis = state["analysis"]
    filename = issue.get("affected_file", "")
    file_content = analysis.get("file_contents", {}).get(filename, "")

    prompt = GENERATE_PROMPT.format(
        issue=json.dumps(issue, indent=2),
        filename=filename,
        file_content=file_content[:3000],
    )

    response = get_llm(temperature=0.1).invoke(prompt)
    result = _parse_json_response(response.content)

    logger.info("Generated patch for %s", filename or "<unknown>")
    return {"current_patch": result.get("patch", "")}


def _parse_json_response(raw_content: str) -> dict:
    try:
        return json.loads(raw_content)
    except json.JSONDecodeError:
        import re

        match = re.search(r"\{.*\}", raw_content, re.DOTALL)
        if not match:
            return {"patch": "", "explanation": ""}
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return {"patch": "", "explanation": ""}
