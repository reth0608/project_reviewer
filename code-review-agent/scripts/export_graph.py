from pathlib import Path

from agent.graph import get_graph


def main() -> None:
    graph = get_graph()
    png = graph.get_graph().draw_mermaid_png()
    output_path = Path("docs/architecture.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(png)
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()
