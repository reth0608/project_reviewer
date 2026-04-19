from sandbox.patch_applicator import apply_unified_diff


def test_apply_unified_diff_replaces_line() -> None:
    original = "def add(a, b):\n    return a - b\n"
    patch = (
        "--- a/solution.py\n"
        "+++ b/solution.py\n"
        "@@ -1,2 +1,2 @@\n"
        " def add(a, b):\n"
        "-    return a - b\n"
        "+    return a + b\n"
    )

    patched = apply_unified_diff(original, patch)
    assert "return a + b" in patched
