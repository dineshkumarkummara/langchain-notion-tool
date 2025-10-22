#!/usr/bin/env python3
"""Find a Notion spec and append a decision log entry."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Optional

from langchain_notion_tools import NotionSearchTool, NotionWriteTool, from_text


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        if not line or line.strip().startswith("#"):
            continue
        key, _, value = line.partition("=")
        if key and value and key not in os.environ:
            os.environ[key.strip()] = value.strip()


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Append a decision log to a Notion spec page")
    parser.add_argument("query", help="Search query used to locate the spec")
    parser.add_argument("decision_markdown", help="Markdown text describing the decision")
    parser.add_argument("--filter", help="Optional JSON filter forwarded to the Notion search API")
    parser.add_argument("--env", default=".env", help="Path to a .env file with NOTION_API_TOKEN")
    parser.add_argument("--dry-run", action="store_true", help="Preview the update without writing")
    args = parser.parse_args(argv)

    _load_dotenv(Path(args.env))

    tool = NotionSearchTool()
    filter_payload = json.loads(args.filter) if args.filter else None
    results = tool.run(query=args.query, filter=filter_payload)
    if not results:
        raise SystemExit("No matching pages found")

    page = results[0]
    print(f"Posting decision log to {page['title']} ({page['id']})")

    blocks = from_text(args.decision_markdown)
    writer = NotionWriteTool()
    response = writer.run(
        update={"page_id": page["id"], "mode": "append"},
        blocks=blocks,
        is_dry_run=args.dry_run,
    )
    print(response["summary"])
    if response.get("url"):
        print("URL:", response["url"])
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
