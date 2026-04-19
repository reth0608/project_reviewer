import json
import logging

from agent.llm import get_llm
from agent.state import AgentState

logger = logging.getLogger(__name__)

PLAN_PROMPT = """You are a senior code reviewer. You have been given the following
analysis of a GitHub Pull Request.

ANALYSIS SUMMARY:
{summary}

CHANGED FUNCTIONS:
{changed_functions}

STATIC ANALYSIS ISSUES:
{static_issues}

RAW DIFF:
{raw_diff}

Your task:
1. Identify the SINGLE most impactful issue to fix in this iteration.
   Focus on: security vulnerabilities, correctness bugs, type errors.
   Ignore: style, naming, minor lint warnings.
2. If no meaningful issue exists, set "no_issue": true.

Respond ONLY with valid JSON in this format:
{{
  "issue_title": "Short description of the issue",
  "issue_explanation": "Why this is a problem",
  "affected_file": "filename.py",
  "affected_function": "function_name",
  "severity": "high|medium|low",
  "no_issue": false
}}"""


def plan_node(state: AgentState) -> dict:
    analysis = state["analysis"]
    prompt = PLAN_PROMPT.format(
        summary=analysis.get("summary", ""),
        changed_functions=json.dumps(analysis.get("changed_functions", []), indent=2),
        static_issues=json.dumps(analysis.get("all_static_issues", [])[:10], indent=2),
        raw_diff="\n".join(list(analysis.get("raw_diffs", {}).values())[:3]),
    )

    response = get_llm().invoke(prompt)
    plan = _parse_json_response(response.content, default={"no_issue": True})
    logger.info("Plan iteration %s: %s", state["iteration"], plan.get("issue_title"))

    issues = list(state.get("review_issues", []))
    if not plan.get("no_issue"):
        issues.append(plan)

    return {
        "current_issue": json.dumps(plan),
        "review_issues": issues,
        "approved": bool(plan.get("no_issue")),
    }


def _parse_json_response(raw_content: str, default: dict) -> dict:
    try:
        return json.loads(raw_content)
    except json.JSONDecodeError:
        import re

        match = re.search(r"\{.*\}", raw_content, re.DOTALL)
        if not match:
            return default
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return default
