# MIT License
#
# Copyright (c) 2024 Dinesh
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Command line utilities for langchain-notion-tools."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Optional

from .blocks import from_text
from .exceptions import NotionConfigurationError
from .tools import NotionSearchTool, NotionWriteTool

__all__ = ["notion_search_main", "notion_write_main"]


def _load_json(value: str, *, description: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:  # pragma: no cover - CLI validation
        raise SystemExit(f"Invalid JSON for {description}: {exc}") from exc


def _load_json_file(path: Path, *, description: str) -> Any:
    if not path.exists():  # pragma: no cover - CLI validation
        raise SystemExit(f"{description} file not found: {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:  # pragma: no cover - CLI validation
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def _print_json(data: Any) -> None:
    json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


def notion_search_main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point for the ``notion-search`` command."""

    parser = argparse.ArgumentParser(description="Search Notion pages and databases")
    parser.add_argument("--query", help="Full-text query to run.")
    parser.add_argument("--page-id", help="Retrieve a single page by ID.")
    parser.add_argument("--database-id", help="Query a database by ID.")
    parser.add_argument(
        "--filter",
        help="JSON object forwarded to Notion's search or database filter API.",
    )
    args = parser.parse_args(argv)

    provided = [opt for opt in (args.query, args.page_id, args.database_id) if opt]
    if len(provided) != 1:
        parser.error("Provide exactly one of --query, --page-id, or --database-id")

    filter_payload = _load_json(args.filter, description="filter") if args.filter else None
    if filter_payload is not None and not isinstance(filter_payload, dict):
        parser.error("--filter must be a JSON object")

    tool = NotionSearchTool()
    results = tool.invoke(
        {
            "query": args.query,
            "page_id": args.page_id,
            "database_id": args.database_id,
            "filter": filter_payload,
        }
    )
    _print_json(results)
    return 0


def notion_write_main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point for the ``notion-write`` command."""

    parser = argparse.ArgumentParser(description="Create or update Notion pages")
    parser.add_argument("--title", help="Title for newly created pages.")
    parser.add_argument("--parent-page", help="Parent page ID for create operations.")
    parser.add_argument("--parent-database", help="Parent database ID for create operations.")
    parser.add_argument("--update-page", help="Existing page ID to update.")
    parser.add_argument(
        "--update-mode",
        choices=["append", "replace"],
        default="append",
        help="Whether to append or replace blocks when updating.",
    )
    parser.add_argument(
        "--properties",
        help="JSON object representing Notion property payloads.",
    )
    parser.add_argument(
        "--blocks-json",
        help="JSON array of Notion blocks to send.",
    )
    parser.add_argument(
        "--blocks-file",
        type=Path,
        help="Path to a JSON file containing an array of blocks.",
    )
    parser.add_argument(
        "--blocks-from-text",
        help="Markdown-like text that will be converted to Notion blocks using from_text().",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Render a summary without calling the Notion API.",
    )
    args = parser.parse_args(argv)

    parent = None
    if args.parent_page and args.parent_database:
        parser.error("Specify either --parent-page or --parent-database, not both")
    if args.parent_page:
        parent = {"page_id": args.parent_page}
    elif args.parent_database:
        parent = {"database_id": args.parent_database}

    update = None
    if args.update_page:
        update = {"page_id": args.update_page, "mode": args.update_mode}

    properties = _load_json(args.properties, description="properties") if args.properties else None
    if properties is not None and not isinstance(properties, dict):
        parser.error("--properties must be a JSON object")

    blocks = None
    sources = [bool(args.blocks_json), bool(args.blocks_file), bool(args.blocks_from_text)]
    if sum(sources) > 1:
        parser.error("Use only one of --blocks-json, --blocks-file, or --blocks-from-text")
    if args.blocks_json:
        blocks = _load_json(args.blocks_json, description="blocks")
    elif args.blocks_file:
        blocks = _load_json_file(args.blocks_file, description="blocks")
    elif args.blocks_from_text:
        blocks = from_text(args.blocks_from_text)

    if blocks is not None and not isinstance(blocks, list):
        parser.error("Blocks payload must be a JSON array")
    if isinstance(blocks, list) and not all(isinstance(item, dict) for item in blocks):
        parser.error("Blocks array must contain JSON objects")

    tool = NotionWriteTool()
    try:
        result = tool.invoke(
            {
                "title": args.title,
                "parent": parent,
                "blocks": blocks,
                "update": update,
                "properties": properties,
                "is_dry_run": args.dry_run,
            }
        )
    except NotionConfigurationError as exc:  # pragma: no cover - CLI validation path
        parser.error(str(exc))
    _print_json(result)
    return 0


if __name__ == "__main__":  # pragma: no cover
    if Path(sys.argv[0]).name == "notion-write":
        sys.exit(notion_write_main())
    sys.exit(notion_search_main())
