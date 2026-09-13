#!/usr/bin/env python3
import argparse
from pathlib import Path
import re
import sys

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.agent import agent
from agent.utils import get_mermaid_graph


def clean_mermaid_for_github(raw_mermaid: str) -> str:
    """Cleans up raw LangGraph mermaid markup for optimal GitHub markdown rendering."""
    cleaned = raw_mermaid.replace("<p>__start__</p>", "Start")
    cleaned = cleaned.replace("<p>__end__</p>", "End")
    return cleaned.strip()


def update_readme(mermaid_code: str, readme_path: Path) -> bool:
    """Updates or inserts the Mermaid graph into README.md."""
    content = readme_path.read_text(encoding="utf-8")
    mermaid_block = f"```mermaid\n{mermaid_code}\n```"

    pattern = r"```mermaid\n[\s\S]*?\n```"
    if re.search(pattern, content):
        new_content = re.sub(pattern, mermaid_block, content, count=1)
    else:
        # Insert right after the top title & intro paragraph
        lines = content.splitlines(keepends=True)
        insert_idx = None
        for i, line in enumerate(lines):
            if line.startswith("<details>") or line.startswith("## "):
                insert_idx = i
                break

        if insert_idx is not None:
            new_content = (
                "".join(lines[:insert_idx])
                + mermaid_block
                + "\n\n"
                + "".join(lines[insert_idx:])
            )
        else:
            new_content = content + "\n\n" + mermaid_block + "\n"

    readme_path.write_text(new_content, encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Generate Mermaid graph from LangGraph agent and update README.md."
    )
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Print mermaid code to stdout without modifying README.md",
    )
    parser.add_argument(
        "--readme",
        type=str,
        default="README.md",
        help="Path to README.md file (default: README.md)",
    )
    args = parser.parse_args()

    mermaid_code = clean_mermaid_for_github(get_mermaid_graph(agent))

    if args.print_only:
        print(f"```mermaid\n{mermaid_code}\n```")
        return

    readme_path = Path(args.readme)
    if not readme_path.exists():
        print(f"Error: {readme_path} does not exist.")
        sys.exit(1)

    update_readme(mermaid_code, readme_path)
    print(f"Successfully generated Mermaid graph and updated {readme_path}!")


if __name__ == "__main__":
    main()
