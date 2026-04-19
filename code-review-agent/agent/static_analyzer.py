import json
import os
import subprocess
import tempfile
from dataclasses import dataclass


@dataclass
class StaticIssue:
    filename: str
    line: int
    rule_id: str
    message: str
    severity: str


def run_ruff(filename: str, source: str) -> list[StaticIssue]:
    with tempfile.NamedTemporaryFile(
        suffix=".py", mode="w", delete=False, encoding="utf-8"
    ) as handle:
        handle.write(source)
        tmp = handle.name

    try:
        result = subprocess.run(
            ["ruff", "check", "--output-format", "json", tmp],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        issues: list[StaticIssue] = []
        if result.stdout.strip():
            for item in json.loads(result.stdout):
                issues.append(
                    StaticIssue(
                        filename=filename,
                        line=item["location"]["row"],
                        rule_id=item["code"] or "RUF000",
                        message=item["message"],
                        severity="warning",
                    )
                )
        return issues
    except Exception:
        return []
    finally:
        os.unlink(tmp)


def run_mypy(filename: str, source: str) -> list[StaticIssue]:
    with tempfile.NamedTemporaryFile(
        suffix=".py", mode="w", delete=False, encoding="utf-8"
    ) as handle:
        handle.write(source)
        tmp = handle.name

    try:
        result = subprocess.run(
            ["mypy", "--ignore-missing-imports", "--no-error-summary", tmp],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        issues: list[StaticIssue] = []
        for line in result.stdout.splitlines():
            parts = line.split(":", 3)
            if len(parts) < 4:
                continue
            try:
                lineno = int(parts[1])
            except ValueError:
                continue
            severity = "error" if "error" in parts[2] else "warning"
            issues.append(
                StaticIssue(
                    filename=filename,
                    line=lineno,
                    rule_id="mypy",
                    message=parts[3].strip(),
                    severity=severity,
                )
            )
        return issues
    except Exception:
        return []
    finally:
        os.unlink(tmp)
