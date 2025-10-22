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

"""Toolkit factory for Notion tools."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Optional

from .client import NotionClientBundle, create_client_bundle
from .config import NotionClientSettings
from .tools import NotionSearchTool, NotionWriteTool

__all__ = ["NotionToolkit", "create_toolkit"]


@dataclass
class NotionToolkit:
    """Container bundling preconfigured Notion tools."""

    settings: NotionClientSettings
    bundle: NotionClientBundle
    search: NotionSearchTool
    write: NotionWriteTool

    @property
    def tools(self) -> Sequence[NotionSearchTool | NotionWriteTool]:
        return (self.search, self.write)


def create_toolkit(
    *,
    api_token: Optional[str] = None,
    default_parent_page_id: Optional[str] = None,
    settings: Optional[NotionClientSettings] = None,
    env: Optional[Mapping[str, str]] = None,
) -> NotionToolkit:
    """Build a NotionToolkit with shared clients for both tools."""

    resolved_settings = NotionClientSettings.resolve(
        api_token=api_token,
        default_parent_page_id=default_parent_page_id,
        settings=settings,
        env=env,
    )
    bundle = create_client_bundle(settings=resolved_settings)
    search = NotionSearchTool(settings=resolved_settings, client=bundle.client, async_client=bundle.async_client)
    write = NotionWriteTool(settings=resolved_settings, client=bundle.client, async_client=bundle.async_client)
    return NotionToolkit(settings=resolved_settings, bundle=bundle, search=search, write=write)
