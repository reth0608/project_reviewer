def format_github_comment(state: dict) -> str:
    issues = state.get("review_issues", [])
    patch = state.get("current_patch", "")
    exec_result = state.get("execution_result", {})
    escalated = state.get("escalate", False)

    n_issues = len(issues)
    n_fixed = 1 if state.get("approved") else 0
    n_human = max(n_issues - n_fixed, 0)

    lines = [
        "## Code review agent",
        "",
        "| Issues found | Auto-fixed | Needs review |",
        "|---|---|---|",
        f"| {n_issues} | {n_fixed} | {n_human} |",
        "",
    ]

    if issues:
        lines.append("### Issues found")
        for issue in issues:
            severity = issue.get("severity", "medium").upper()
            lines.append(
                f"- **[{severity}]** `{issue.get('affected_file')}` - {issue.get('issue_title')}"
            )
            lines.append(f"  > {issue.get('issue_explanation', '')}")
        lines.append("")

    if state.get("approved") and patch:
        n_pass = exec_result.get("passed_tests", 0)
        n_total = exec_result.get("total_tests", 0)
        lines.extend(
            [
                "### Auto-fix (verified)",
                "",
                "```diff",
                patch,
                "```",
                "",
                f"Tests passed: {n_pass}/{n_total} in sandboxed execution.",
                "",
            ]
        )

    if escalated:
        lines.extend(
            [
                "### Flagged for human review",
                "",
                "The agent could not generate a verified fix within the iteration budget.",
                "See the LangSmith trace for the full reasoning history.",
                "",
            ]
        )

    lines.extend(
        [
            "---",
            f"*Ran: ruff, mypy, AST diff analysis, Docker sandbox, {state.get('iteration', 0)} iteration(s)*",
        ]
    )
    return "\n".join(lines)
