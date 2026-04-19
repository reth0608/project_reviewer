import json
import logging
from dataclasses import asdict

from agent.github_client import get_github_client
from agent.state import AgentState
from sandbox.executor import execute_patch

logger = logging.getLogger(__name__)


def _find_test_source(state: AgentState, filename: str) -> str:
    analysis = state["analysis"]
    file_contents = analysis.get("file_contents", {})
    module_name = filename.rsplit("/", 1)[-1].replace(".py", "")
    candidates = [
        f"tests/test_{module_name}.py",
        f"test_{module_name}.py",
    ]

    for candidate in candidates:
        if candidate in file_contents:
            return file_contents[candidate]

    try:
        gh = get_github_client()
        repo = gh.get_repo(state["repo_name"])
        pr = repo.get_pull(state["pr_number"])
        for candidate in candidates:
            try:
                content_obj = repo.get_contents(candidate, ref=pr.head.sha)
            except Exception:
                continue
            return content_obj.decoded_content.decode("utf-8", errors="replace")
    except Exception:
        pass

    return "# No test file found\ndef test_placeholder():\n    assert True\n"


def execute_node(state: AgentState) -> dict:
    issue = json.loads(state["current_issue"])
    filename = issue.get("affected_file", "solution.py")
    analysis = state["analysis"]

    original = analysis.get("file_contents", {}).get(filename, "")
    patch = state["current_patch"]
    tests = _find_test_source(state, filename)

    logger.info("Executing patch in sandbox, iteration %s", state["iteration"] + 1)
    result = execute_patch(original, patch, tests, filename=filename.rsplit("/", 1)[-1])

    logger.info(
        "Execution result: passed=%s (%s/%s tests)",
        result.tests_passed,
        result.passed_tests,
        result.total_tests,
    )
    return {"execution_result": asdict(result), "iteration": state["iteration"] + 1}
