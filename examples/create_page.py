#!/usr/bin/env python3
"""Create a new Notion page from Markdown text."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from langchain_notion_tools import NotionWriteTool, from_text


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        if not line or line.strip().startswith("#"):
            continue
        key, _, value = line.partition("=")
        if key and value and key not in os.environ:
            os.environ[key.strip()] = value.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a Notion page from Markdown content")
    parser.add_argument("parent", help="Parent page or database ID")
    parser.add_argument("title", help="Title for the new page")
    parser.add_argument("markdown", help="Path to a Markdown file or '-' to read stdin")
    parser.add_argument("--database", action="store_true", help="Treat the parent ID as a database.")
    parser.add_argument("--dry-run", action="store_true", help="Render a preview without writing")
    parser.add_argument("--env", default=".env", help="Path to a .env file with NOTION_API_TOKEN")
    args = parser.parse_args(argv)

    _load_dotenv(Path(args.env))

    if args.markdown == "-":
        markdown = Path("/dev/stdin").read_text()
    else:
        markdown = Path(args.markdown).read_text()

    blocks = from_text(markdown)
    parent = {"database_id": args.parent} if args.database else {"page_id": args.parent}

    tool = NotionWriteTool()
    result = tool.run(
        title=args.title,
        parent=parent,
        blocks=blocks,
        is_dry_run=args.dry_run,
    )
    print(result["summary"])
    if result.get("url"):
        print("URL:", result["url"])
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
