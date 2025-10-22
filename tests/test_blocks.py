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

import json
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from langchain_notion_tools.blocks import (
    ALLOWED_BLOCK_TYPES,
    MAX_BLOCKS,
    MAX_TOTAL_TEXT_LENGTH,
    code,
    from_text,
    paragraph,
    sanitize_blocks,
)
from langchain_notion_tools.exceptions import NotionConfigurationError

GOLDEN_TEXT = """# Title

- Item one
- Item two

```python
print("Hello")
```
"""


def _load_golden() -> list[dict]:
    path = Path(__file__).parent / "golden_blocks.json"
    return json.loads(path.read_text())


def test_from_text_matches_golden() -> None:
    expected = _load_golden()
    assert from_text(GOLDEN_TEXT) == expected


@given(st.text(max_size=50))
def test_paragraph_round_trip(text: str) -> None:
    block = paragraph(text)
    sanitized = sanitize_blocks([block])
    assert sanitized[0]["paragraph"]["rich_text"][0]["text"]["content"] == text


def test_sanitize_blocks_enforces_allowlist() -> None:
    invalid_block = {"type": "unsupported"}
    with pytest.raises(NotionConfigurationError):
        sanitize_blocks([invalid_block])


def test_sanitize_blocks_limits_length() -> None:
    blocks = [paragraph("a" * 100)] * (MAX_BLOCKS + 1)
    with pytest.raises(NotionConfigurationError):
        sanitize_blocks(blocks)


def test_sanitize_blocks_limits_text_length() -> None:
    long_text = 'a' * (MAX_TOTAL_TEXT_LENGTH + 1)
    with pytest.raises(NotionConfigurationError):
        sanitize_blocks([paragraph(long_text)])


def test_code_block_links_removed() -> None:
    block = code("x", language="python")
    block["code"]["rich_text"][0]["text"]["link"] = {"url": "https://example.com"}
    sanitized = sanitize_blocks([block])
    assert "link" not in sanitized[0]["code"]["rich_text"][0]["text"]


def test_allowed_block_types_cover_helpers() -> None:
    helper_types = {"paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item", "to_do", "toggle", "callout", "quote", "code"}
    assert helper_types <= ALLOWED_BLOCK_TYPES
