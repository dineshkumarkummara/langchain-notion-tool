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

from collections.abc import Mapping
from typing import Any

import pytest

from langchain_notion_tools.client import (
    NotionClientBundle,
    create_async_client,
    create_client_bundle,
    create_sync_client,
)
from langchain_notion_tools.config import NotionClientSettings


class DummySyncClient:
    def __init__(self, *, auth: str, **kwargs: Any) -> None:
        self.auth = auth
        self.kwargs = kwargs


class DummyAsyncClient:
    def __init__(self, *, auth: str, **kwargs: Any) -> None:
        self.auth = auth
        self.kwargs = kwargs


@pytest.fixture(autouse=True)
def patch_client_classes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "langchain_notion_tools.client._load_client_classes",
        lambda: (DummySyncClient, DummyAsyncClient),
    )


def test_create_sync_client_returns_existing_instance() -> None:
    existing = DummySyncClient(auth="token")
    assert (
        create_sync_client(client=existing, settings=NotionClientSettings(api_token="t"))
        is existing
    )


def test_create_sync_client_constructs_new_instance() -> None:
    settings = NotionClientSettings(api_token="token", client_timeout=42.0, max_retries=7)
    client = create_sync_client(settings=settings)
    assert isinstance(client, DummySyncClient)
    assert client.auth == "token"
    assert client.kwargs["client_options"]["timeout"] == 42.0
    assert client.kwargs["client_options"]["max_retries"] == 7


def test_create_sync_client_respects_custom_client_options() -> None:
    settings = NotionClientSettings(api_token="token")
    client = create_sync_client(
        settings=settings,
        client_options={"timeout": 5, "headers": {"X-Test": "1"}},
    )
    options = client.kwargs["client_options"]
    assert options["timeout"] == 5
    assert options["headers"] == {"X-Test": "1"}
    assert options["max_retries"] == settings.max_retries


def test_create_sync_client_uses_env(monkeypatch: pytest.MonkeyPatch) -> None:
    env: Mapping[str, str] = {"NOTION_API_TOKEN": "env-token"}
    client = create_sync_client(env=env)
    assert isinstance(client, DummySyncClient)
    assert client.auth == "env-token"


def test_create_async_client_constructs_new_instance() -> None:
    settings = NotionClientSettings(api_token="token", client_timeout=12.0, max_retries=2)
    client = create_async_client(settings=settings)
    assert isinstance(client, DummyAsyncClient)
    assert client.auth == "token"
    options = client.kwargs["client_options"]
    assert options["timeout"] == 12.0
    assert options["max_retries"] == 2


def test_create_async_client_respects_custom_options() -> None:
    settings = NotionClientSettings(api_token="token")
    client = create_async_client(
        settings=settings,
        client_options={"timeout": 9, "max_retries": 1},
    )
    options = client.kwargs["client_options"]
    assert options["timeout"] == 9
    assert options["max_retries"] == 1


def test_create_client_bundle_reuses_provided_instances() -> None:
    settings = NotionClientSettings(api_token="token")
    sync = DummySyncClient(auth="token")
    async_client = DummyAsyncClient(auth="token")
    bundle = create_client_bundle(
        settings=settings,
        client=sync,
        async_client=async_client,
    )
    assert bundle == NotionClientBundle(sync, async_client)


def test_create_client_bundle_builds_clients_with_kwargs() -> None:
    bundle = create_client_bundle(
        api_token="token",
        client_kwargs={"client_options": {"timeout": 1, "max_retries": 2}},
        async_client_kwargs={"client_options": {"timeout": 3, "max_retries": 4}},
    )
    assert isinstance(bundle.client, DummySyncClient)
    assert isinstance(bundle.async_client, DummyAsyncClient)
    assert bundle.client.kwargs["client_options"]["timeout"] == 1
    assert bundle.client.kwargs["client_options"]["max_retries"] == 2
    assert bundle.async_client.kwargs["client_options"]["timeout"] == 3
    assert bundle.async_client.kwargs["client_options"]["max_retries"] == 4
