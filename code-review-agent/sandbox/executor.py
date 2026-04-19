import logging
import os
import tempfile
from dataclasses import dataclass

import docker

from sandbox.patch_applicator import apply_unified_diff

logger = logging.getLogger(__name__)
SANDBOX_IMAGE = "code-review-sandbox:latest"
TIMEOUT_SECONDS = 30
MEMORY_LIMIT = "256m"


@dataclass
class ExecutionResult:
    tests_passed: bool
    total_tests: int
    passed_tests: int
    failed_tests: int
    output: str
    error: str
    timed_out: bool = False


def execute_patch(
    original_source: str,
    patch: str,
    test_source: str,
    filename: str = "solution.py",
) -> ExecutionResult:
    """Apply a patch and run tests inside a Docker sandbox."""
    try:
        patched = apply_unified_diff(original_source, patch)
    except Exception as exc:
        return ExecutionResult(
            tests_passed=False,
            total_tests=0,
            passed_tests=0,
            failed_tests=0,
            output="",
            error=f"Patch application failed: {exc}",
        )

    client = docker.from_env()

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, filename), "w", encoding="utf-8") as handle:
            handle.write(patched)
        with open(
            os.path.join(tmpdir, "test_solution.py"), "w", encoding="utf-8"
        ) as handle:
            handle.write(test_source)

        try:
            raw = client.containers.run(
                SANDBOX_IMAGE,
                command="pytest test_solution.py -v --tb=short --timeout=20",
                volumes={tmpdir: {"bind": "/app", "mode": "rw"}},
                working_dir="/app",
                mem_limit=MEMORY_LIMIT,
                network_disabled=True,
                remove=True,
                stdout=True,
                stderr=True,
            )
            output = raw.decode("utf-8", errors="replace")
            return _parse_pytest_output(output)
        except docker.errors.ContainerError as exc:
            output = (
                exc.stderr.decode("utf-8", errors="replace") if exc.stderr else str(exc)
            )
            return _parse_pytest_output(output)
        except Exception as exc:
            timed_out = "timeout" in str(exc).lower()
            return ExecutionResult(
                tests_passed=False,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                output="",
                error=str(exc),
                timed_out=timed_out,
            )


def _parse_pytest_output(output: str) -> ExecutionResult:
    import re

    passed = failed = 0
    for line in output.splitlines():
        passed_match = re.search(r"(\d+) passed", line)
        if passed_match:
            passed = int(passed_match.group(1))
        failed_match = re.search(r"(\d+) failed", line)
        if failed_match:
            failed = int(failed_match.group(1))

    total = passed + failed
    return ExecutionResult(
        tests_passed=(total > 0 and failed == 0),
        total_tests=total,
        passed_tests=passed,
        failed_tests=failed,
        output=output,
        error="",
    )
