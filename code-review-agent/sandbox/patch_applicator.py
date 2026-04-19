import re


def apply_unified_diff(original: str, patch: str) -> str:
    """
    Apply a limited unified diff patch string to the original source.
    Returns the patched source or raises ValueError on failure.
    """
    if not patch.strip():
        return original

    original_lines = original.splitlines(keepends=True)
    result_lines = list(original_lines)
    offset = 0

    hunk_pattern = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
    patch_lines = patch.splitlines(keepends=True)

    i = 0
    while i < len(patch_lines):
        match = hunk_pattern.match(patch_lines[i])
        if not match:
            i += 1
            continue

        old_start = int(match.group(1)) - 1
        i += 1

        removals: list[str] = []
        additions: list[str] = []
        while i < len(patch_lines) and not hunk_pattern.match(patch_lines[i]):
            line = patch_lines[i]
            if line.startswith("-") and not line.startswith("---"):
                removals.append(line[1:])
            elif line.startswith("+") and not line.startswith("+++"):
                additions.append(line[1:])
            i += 1

        pos = old_start + offset
        result_lines[pos : pos + len(removals)] = additions
        offset += len(additions) - len(removals)

    return "".join(result_lines)
