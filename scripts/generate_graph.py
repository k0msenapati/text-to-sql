#!/usr/bin/env python3
import argparse
from pathlib import Path
import re
import sys

# Ensure project root and src are on sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "src"))
sys.path.insert(0, str(root_dir))

from text_to_sql.graph import agent  # noqa: E402
from text_to_sql.utils import get_mermaid_graph  # noqa: E402


def clean_mermaid_for_github(raw_mermaid: str) -> str:
    """
    Cleans up raw LangGraph mermaid markup for optimal GitHub rendering:
    - Strips YAML config frontmatter
    - Strips all classDef, style, and color definitions
    - Removes class annotations (:::className) and HTML tags
    - Normalizes start and end nodes into standard GitHub-friendly shapes
    - Produces a clean normal graph with no colors or extra styles for GitHub
    """
    lines = []
    in_yaml = False
    for line in raw_mermaid.splitlines():
        trimmed = line.strip()
        if trimmed == "---":
            in_yaml = not in_yaml
            continue
        if in_yaml:
            continue
        if trimmed.startswith(("classDef", "style", "linkStyle", "class ")):
            continue

        # Remove class attachments like :::first, :::last, :::default
        cleaned_line = re.sub(r":::\w+", "", line)
        # Remove any HTML tags like <p>...</p>
        cleaned_line = re.sub(r"</?[a-zA-Z0-9]+[^>]*>", "", cleaned_line)
        # Normalize start and end tokens
        cleaned_line = cleaned_line.replace("__start__", "Start").replace(
            "__end__", "End"
        )
        if cleaned_line.strip():
            lines.append(cleaned_line)

    result_lines = []
    header_found = False
    for line in lines:
        result_lines.append(line)
        if not header_found and (
            "graph TD" in line or "graph LR" in line or "flowchart" in line
        ):
            header_found = True
            if not any("Start([" in entry for entry in lines):
                result_lines.append("\tStart([Start])")
            if not any("End([" in entry for entry in lines):
                result_lines.append("\tEnd([End])")

    return "\n".join(result_lines).strip()


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

    mermaid_code = clean_mermaid_for_github(get_mermaid_graph(agent, with_styles=False))

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
