from dataclasses import dataclass

import tree_sitter_python as tspython
from tree_sitter import Language, Parser

PY_LANGUAGE = Language(tspython.language())
_parser = Parser(PY_LANGUAGE)


@dataclass
class FunctionInfo:
    name: str
    start_line: int
    end_line: int
    source: str
    is_changed: bool = False


def parse_changed_functions(full_source: str, patch: str) -> list[FunctionInfo]:
    """Return top-level functions and mark those touched by the patch."""
    if not full_source.strip():
        return []

    tree = _parser.parse(full_source.encode("utf-8"))
    changed_lines = _extract_changed_lines(patch)

    functions: list[FunctionInfo] = []
    for node in tree.root_node.children:
        function_node = _unwrap_function_node(node)
        if function_node is None:
            continue

        start = function_node.start_point[0] + 1
        end = function_node.end_point[0] + 1
        source = full_source[function_node.start_byte : function_node.end_byte]
        name_node = function_node.child_by_field_name("name")
        name = name_node.text.decode() if name_node else "<unknown>"

        functions.append(
            FunctionInfo(
                name=name,
                start_line=start,
                end_line=end,
                source=source,
                is_changed=bool(changed_lines.intersection(range(start, end + 1))),
            )
        )

    return functions


def _unwrap_function_node(node):
    if node.type == "function_definition":
        return node
    if node.type == "decorated_definition":
        for child in node.children:
            if child.type == "function_definition":
                return child
    return None


def _extract_changed_lines(patch: str) -> set[int]:
    """Parse unified diff hunks to find changed line numbers in the new file."""
    changed: set[int] = set()
    current_line = 0

    for line in patch.splitlines():
        if line.startswith("@@"):
            try:
                new_part = line.split("+", 1)[1].split("@@", 1)[0].strip()
                start_str = new_part.split(",", 1)[0]
                current_line = int(start_str)
            except (IndexError, ValueError):
                current_line = 0
        elif line.startswith("+") and not line.startswith("+++"):
            changed.add(current_line)
            current_line += 1
        elif line.startswith("-") and not line.startswith("---"):
            continue
        else:
            current_line += 1

    return changed
