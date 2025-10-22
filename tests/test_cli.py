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

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

import pytest

from langchain_notion_tools import cli


class _CaptureSearchTool:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def invoke(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        self.calls.append(payload)
        return [{"ok": True}]


class _CaptureWriteTool:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(payload)
        return {"status": "ok", "summary": "done"}


def _capture_stdout(monkeypatch: pytest.MonkeyPatch) -> io.StringIO:
    buffer = io.StringIO()
    monkeypatch.setattr(cli.sys, "stdout", buffer)
    return buffer


def test_notion_search_main_with_query(monkeypatch: pytest.MonkeyPatch) -> None:
    tool = _CaptureSearchTool()
    monkeypatch.setattr(cli, "NotionSearchTool", lambda: tool)
    stdout = _capture_stdout(monkeypatch)

    exit_code = cli.notion_search_main(
        ["--query", "roadmap", "--filter", '{"property": "Status"}']
    )

    assert exit_code == 0
    assert tool.calls == [
        {
            "query": "roadmap",
            "page_id": None,
            "database_id": None,
            "filter": {"property": "Status"},
        }
    ]
    assert json.loads(stdout.getvalue()) == [{"ok": True}]


def test_notion_search_main_with_page(monkeypatch: pytest.MonkeyPatch) -> None:
    tool = _CaptureSearchTool()
    monkeypatch.setattr(cli, "NotionSearchTool", lambda: tool)
    stdout = _capture_stdout(monkeypatch)

    exit_code = cli.notion_search_main(["--page-id", "page-123"])

    assert exit_code == 0
    assert tool.calls[0]["page_id"] == "page-123"
    assert json.loads(stdout.getvalue()) == [{"ok": True}]


def test_notion_write_main_with_blocks_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    tool = _CaptureWriteTool()
    monkeypatch.setattr(cli, "NotionWriteTool", lambda: tool)
    stdout = _capture_stdout(monkeypatch)

    blocks_path = tmp_path / "blocks.json"
    blocks_path.write_text(
        json.dumps(
            [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": []},
                }
            ]
        )
    )

    exit_code = cli.notion_write_main(
        [
            "--title",
            "Daily Notes",
            "--parent-page",
            "parent-1",
            "--blocks-file",
            str(blocks_path),
            "--properties",
            '{"Status": {"select": {"name": "Draft"}}}',
            "--dry-run",
        ]
    )

    assert exit_code == 0
    assert tool.calls == [
        {
            "title": "Daily Notes",
            "parent": {"page_id": "parent-1"},
            "blocks": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": []},
                }
            ],
            "update": None,
            "properties": {"Status": {"select": {"name": "Draft"}}},
            "is_dry_run": True,
        }
    ]
    assert json.loads(stdout.getvalue()) == {"status": "ok", "summary": "done"}


def test_notion_write_main_blocks_from_text(monkeypatch: pytest.MonkeyPatch) -> None:
    tool = _CaptureWriteTool()
    monkeypatch.setattr(cli, "NotionWriteTool", lambda: tool)
    stdout = _capture_stdout(monkeypatch)
    monkeypatch.setattr(cli, "from_text", lambda text: [{"text": text}])

    exit_code = cli.notion_write_main(
        [
            "--update-page",
            "page-42",
            "--blocks-from-text",
            "### Heading",
        ]
    )

    assert exit_code == 0
    assert tool.calls[0]["update"] == {"page_id": "page-42", "mode": "append"}
    assert tool.calls[0]["blocks"] == [{"text": "### Heading"}]
    assert json.loads(stdout.getvalue()) == {"status": "ok", "summary": "done"}


def test_notion_write_main_with_database_parent(monkeypatch: pytest.MonkeyPatch) -> None:
    tool = _CaptureWriteTool()
    monkeypatch.setattr(cli, "NotionWriteTool", lambda: tool)
    stdout = _capture_stdout(monkeypatch)

    exit_code = cli.notion_write_main(
        [
            "--parent-database",
            "db-1",
            "--title",
            "Row",
            "--blocks-json",
            '[{"object": "block", "type": "paragraph", "paragraph": {"rich_text": []}}]',
        ]
    )

    assert exit_code == 0
    assert tool.calls[0]["parent"] == {"database_id": "db-1"}
    assert tool.calls[0]["blocks"][0]["type"] == "paragraph"
    assert json.loads(stdout.getvalue()) == {"status": "ok", "summary": "done"}


def test_notion_search_main_requires_single_mode() -> None:
    with pytest.raises(SystemExit):
        cli.notion_search_main([])


def test_notion_search_main_validates_filter_type() -> None:
    with pytest.raises(SystemExit):
        cli.notion_search_main(["--query", "x", "--filter", "[]"])


def test_notion_write_parent_options_are_exclusive() -> None:
    with pytest.raises(SystemExit):
        cli.notion_write_main(["--parent-page", "a", "--parent-database", "b"])


def test_notion_write_blocks_sources_are_mutually_exclusive() -> None:
    with pytest.raises(SystemExit):
        cli.notion_write_main(
            [
                "--parent-page",
                "a",
                "--title",
                "b",
                "--blocks-json",
                "[]",
                "--blocks-from-text",
                "text",
            ]
        )


def test_notion_write_blocks_must_be_array() -> None:
    with pytest.raises(SystemExit):
        cli.notion_write_main(
            ["--parent-page", "a", "--title", "b", "--blocks-json", '{"type": "paragraph"}']
        )


def test_notion_write_blocks_must_contain_objects() -> None:
    with pytest.raises(SystemExit):
        cli.notion_write_main(
            ["--parent-page", "a", "--title", "b", "--blocks-json", "[1, 2, 3]"]
        )


def test_notion_write_properties_must_be_object() -> None:
    with pytest.raises(SystemExit):
        cli.notion_write_main(
            ["--parent-page", "a", "--title", "b", "--properties", '["invalid"]']
        )
