import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
from dotenv import load_dotenv
from github import GithubException

from agent.context_packager import analyse_pr

load_dotenv()


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python .\\scripts\\test_analysis.py <repo> <pr_number>")
        raise SystemExit(1)

    repo = sys.argv[1]
    pr_number = int(sys.argv[2])
    try:
        result = analyse_pr(repo, pr_number)
    except GithubException as exc:
        if exc.status == 404:
            pulls = _list_pull_requests(repo)
            if pulls:
                print(f"PR #{pr_number} was not found in {repo}. Available PRs: {pulls}")
            else:
                print(
                    f"PR #{pr_number} was not found in {repo}. "
                    "This repo currently has no pull requests."
                )
            raise SystemExit(1)
        raise

    print(result.summary)
    print(f"Changed functions: {[item['name'] for item in result.changed_functions]}")
    print(f"Static issues: {len(result.all_static_issues)}")


def _list_pull_requests(repo: str) -> list[int]:
    response = httpx.get(
        f"https://api.github.com/repos/{repo}/pulls?state=all",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "code-review-agent",
        },
        timeout=30.0,
        trust_env=False,
    )
    response.raise_for_status()
    return [item["number"] for item in response.json()]


if __name__ == "__main__":
    main()
