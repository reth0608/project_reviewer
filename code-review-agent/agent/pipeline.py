import logging
import os

from agent.comment_formatter import format_github_comment
from agent.context_packager import analyse_pr
from agent.github_client import get_github_client
from agent.graph import get_graph
from dotenv import load_dotenv

load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = os.environ.get(
    "LANGSMITH_PROJECT", "code-review-agent"
)

logger = logging.getLogger(__name__)


async def run_agent_on_pr(repo_name: str, pr_number: int) -> None:
    logger.info("Starting review for PR #%s in %s", pr_number, repo_name)

    try:
        analysis = analyse_pr(repo_name, pr_number)
    except Exception as exc:  # pragma: no cover - network-backed integration path
        logger.exception("Analysis failed: %s", exc)
        return

    graph = get_graph()
    initial_state = {
        "repo_name": repo_name,
        "pr_number": pr_number,
        "analysis": {
            "summary": analysis.summary,
            "changed_functions": analysis.changed_functions,
            "all_static_issues": analysis.all_static_issues,
            "raw_diffs": analysis.raw_diffs,
            "file_contents": analysis.file_contents,
        },
        "messages": [],
        "current_issue": "",
        "current_patch": "",
        "execution_result": {},
        "iteration": 0,
        "max_iterations": 3,
        "approved": False,
        "escalate": False,
        "review_issues": [],
        "final_comment": "",
    }

    try:
        final_state = await graph.ainvoke(initial_state)
    except Exception as exc:  # pragma: no cover - LLM-backed integration path
        logger.exception("Agent loop failed: %s", exc)
        return

    comment = format_github_comment(final_state)

    try:
        gh = get_github_client()
        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        pr.create_issue_comment(comment)
        logger.info("Comment posted to PR #%s", pr_number)

        conclusion = "success" if final_state.get("approved") else "neutral"
        repo.create_check_run(
            name="code-review-agent",
            head_sha=pr.head.sha,
            status="completed",
            conclusion=conclusion,
            output={
                "title": "Code review complete",
                "summary": comment[:65535],
            },
        )
    except Exception as exc:  # pragma: no cover - network-backed integration path
        logger.warning("Failed to post GitHub outputs: %s", exc)
