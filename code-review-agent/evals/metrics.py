import re

from sandbox.executor import execute_patch
from sandbox.patch_applicator import apply_unified_diff


def measure_pass_at_k(original: str, patch: str, test_code: str, k: int = 3) -> bool:
    """Return True if the patch passes tests within k attempts."""
    for _ in range(k):
        result = execute_patch(original, patch, test_code)
        if result.tests_passed:
            return True
    return False


def measure_hallucination(original: str, patch: str, flagged_lines: list[int]) -> float:
    """
    Return the fraction of patch changes that fall outside flagged lines.
    0.0 is perfectly minimal, 1.0 is entirely off-target.
    """
    del original
    changed_lines = _extract_patch_lines(patch)
    if not changed_lines:
        return 0.0
    flagged_set = set(flagged_lines)
    off_target = [line for line in changed_lines if line not in flagged_set]
    return len(off_target) / len(changed_lines)


def semantic_scope_check(
    original_source: str, patch: str, flagged_function: str
) -> dict[str, object]:
    """
    Check whether the patch only modifies the flagged function.
    Returns a report with touched_functions and scope_violation status.
    """
    import tree_sitter_python as tspython
    from tree_sitter import Language, Parser

    py_language = Language(tspython.language())
    parser = Parser(py_language)

    try:
        patched = apply_unified_diff(original_source, patch)
    except Exception:
        return {
            "scope_violation": True,
            "touched_functions": [],
            "flagged_function": flagged_function,
            "reason": "patch failed",
        }

    orig_tree = parser.parse(original_source.encode("utf-8"))
    patched_tree = parser.parse(patched.encode("utf-8"))

    def get_fn_sources(tree, source: str) -> dict[str, str]:
        functions: dict[str, str] = {}
        for node in tree.root_node.children:
            if node.type != "function_definition":
                continue
            name = node.child_by_field_name("name")
            if name:
                functions[name.text.decode()] = source[node.start_byte : node.end_byte]
        return functions

    orig_functions = get_fn_sources(orig_tree, original_source)
    patched_functions = get_fn_sources(patched_tree, patched)
    touched = [
        name for name, source in patched_functions.items() if orig_functions.get(name) != source
    ]
    violation = any(name != flagged_function for name in touched)

    return {
        "scope_violation": violation,
        "touched_functions": touched,
        "flagged_function": flagged_function,
        "reason": (
            "patch modified functions outside flagged scope" if violation else "ok"
        ),
    }


def _extract_patch_lines(patch: str) -> list[int]:
    lines: list[int] = []
    current = 0
    for line in patch.splitlines():
        if line.startswith("@@"):
            match = re.search(r"\+(\d+)", line)
            if match:
                current = int(match.group(1))
        elif line.startswith("+") and not line.startswith("+++"):
            lines.append(current)
            current += 1
        elif line.startswith("-") and not line.startswith("---"):
            continue
        else:
            current += 1
    return lines
