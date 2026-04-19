from dataclasses import dataclass

from agent.github_client import get_github_client


@dataclass
class ChangedFile:
    filename: str
    patch: str
    full_content: str
    additions: int
    deletions: int
    is_python: bool


def fetch_pr_files(repo_name: str, pr_number: int) -> list[ChangedFile]:
    gh = get_github_client()
    repo = gh.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    results: list[ChangedFile] = []
    for changed_file in pr.get_files():
        if changed_file.status == "removed":
            continue

        try:
            content_obj = repo.get_contents(changed_file.filename, ref=pr.head.sha)
            full_content = content_obj.decoded_content.decode("utf-8", errors="replace")
        except Exception:
            full_content = ""

        results.append(
            ChangedFile(
                filename=changed_file.filename,
                patch=changed_file.patch or "",
                full_content=full_content,
                additions=changed_file.additions,
                deletions=changed_file.deletions,
                is_python=changed_file.filename.endswith(".py"),
            )
        )

    return results
