from __future__ import annotations

import pytest

from langchain_notion_tools.client import NotionClientBundle
from langchain_notion_tools.config import NotionClientSettings
from langchain_notion_tools.toolkit import NotionToolkit, create_toolkit


class DummyClient:
    def __init__(self) -> None:
        self.created = True


class DummyAsyncClient(DummyClient):
    async def close(self) -> None:  # pragma: no cover - not used in tests
        pass


def test_create_toolkit_builds_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_bundle(*, settings: NotionClientSettings, **_: object) -> NotionClientBundle:
        return NotionClientBundle(DummyClient(), DummyAsyncClient())

    monkeypatch.setattr(
        "langchain_notion_tools.toolkit.create_client_bundle",  # type: ignore[attr-defined]
        fake_bundle,
    )
    toolkit = create_toolkit(api_token="token")
    assert isinstance(toolkit.search, type(toolkit.write)) is False
    assert toolkit.tools[0] is toolkit.search
    assert toolkit.tools[1] is toolkit.write
    assert toolkit.search._client is toolkit.write._client  # type: ignore[attr-defined]
    assert toolkit.search._async_client is toolkit.write._async_client  # type: ignore[attr-defined]


def test_toolkit_reuses_settings_and_bundle(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_settings: NotionClientSettings | None = None

    def fake_bundle(*, settings: NotionClientSettings, **_: object) -> NotionClientBundle:
        nonlocal captured_settings
        captured_settings = settings
        return NotionClientBundle(DummyClient(), DummyAsyncClient())

    monkeypatch.setattr(
        "langchain_notion_tools.toolkit.create_client_bundle",  # type: ignore[attr-defined]
        fake_bundle,
    )
    settings = NotionClientSettings(api_token="token", client_timeout=5, max_retries=1)
    toolkit = create_toolkit(settings=settings)
    assert toolkit.settings is settings
    assert captured_settings is settings
    assert isinstance(toolkit, NotionToolkit)
