from __future__ import annotations

from typing import Any, Mapping

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
    settings = NotionClientSettings(api_token="token")
    client = create_sync_client(settings=settings, timeout=5)
    assert isinstance(client, DummySyncClient)
    assert client.auth == "token"
    assert client.kwargs["timeout"] == 5


def test_create_sync_client_uses_env(monkeypatch: pytest.MonkeyPatch) -> None:
    env: Mapping[str, str] = {"NOTION_API_TOKEN": "env-token"}
    client = create_sync_client(env=env)
    assert isinstance(client, DummySyncClient)
    assert client.auth == "env-token"


def test_create_async_client_constructs_new_instance() -> None:
    settings = NotionClientSettings(api_token="token")
    client = create_async_client(settings=settings, timeout=10)
    assert isinstance(client, DummyAsyncClient)
    assert client.auth == "token"
    assert client.kwargs["timeout"] == 10


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
        client_kwargs={"timeout": 1},
        async_client_kwargs={"timeout": 2},
    )
    assert isinstance(bundle.client, DummySyncClient)
    assert isinstance(bundle.async_client, DummyAsyncClient)
    assert bundle.client.kwargs["timeout"] == 1
    assert bundle.async_client.kwargs["timeout"] == 2
