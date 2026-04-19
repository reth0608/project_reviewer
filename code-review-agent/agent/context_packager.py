from dataclasses import asdict, dataclass

from agent.ast_analyzer import parse_changed_functions
from agent.diff_fetcher import fetch_pr_files
from agent.static_analyzer import run_mypy, run_ruff


@dataclass
class PRAnalysis:
    repo_name: str
    pr_number: int
    changed_functions: list[dict]
    all_static_issues: list[dict]
    raw_diffs: dict[str, str]
    file_contents: dict[str, str]
    summary: str


def analyse_pr(repo_name: str, pr_number: int) -> PRAnalysis:
    files = fetch_pr_files(repo_name, pr_number)

    changed_functions: list[dict] = []
    static_issues: list[dict] = []
    raw_diffs: dict[str, str] = {}
    file_contents: dict[str, str] = {}

    for changed_file in files:
        raw_diffs[changed_file.filename] = changed_file.patch
        file_contents[changed_file.filename] = changed_file.full_content

        if changed_file.is_python and changed_file.full_content:
            functions = parse_changed_functions(changed_file.full_content, changed_file.patch)
            for function in functions:
                if function.is_changed:
                    changed_functions.append(
                        {**asdict(function), "filename": changed_file.filename}
                    )

            static_issues.extend(
                asdict(issue) for issue in run_ruff(changed_file.filename, changed_file.full_content)
            )
            static_issues.extend(
                asdict(issue) for issue in run_mypy(changed_file.filename, changed_file.full_content)
            )

    summary = (
        f"PR #{pr_number} in {repo_name} modifies {len(files)} file(s), "
        f"touching {len(changed_functions)} Python function(s). "
        f"Static analysis found {len(static_issues)} issue(s)."
    )

    return PRAnalysis(
        repo_name=repo_name,
        pr_number=pr_number,
        changed_functions=changed_functions,
        all_static_issues=static_issues,
        raw_diffs=raw_diffs,
        file_contents=file_contents,
        summary=summary,
    )
