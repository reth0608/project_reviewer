from agent.comment_formatter import format_github_comment


def test_format_github_comment_includes_issue_summary() -> None:
    comment = format_github_comment(
        {
            "review_issues": [
                {
                    "severity": "high",
                    "affected_file": "app.py",
                    "issue_title": "Missing timeout",
                    "issue_explanation": "Network calls should time out.",
                }
            ],
            "approved": False,
            "iteration": 1,
        }
    )

    assert "Missing timeout" in comment
    assert "| 1 | 0 | 1 |" in comment
