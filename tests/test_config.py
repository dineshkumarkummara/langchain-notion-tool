from __future__ import annotations

import os
from typing import Mapping

import pytest

from langchain_notion_tools.config import (
    NOTION_API_TOKEN_ENV_VAR,
    NOTION_DEFAULT_PARENT_PAGE_ID_ENV_VAR,
    NotionClientSettings,
    redact_token,
)
from langchain_notion_tools.exceptions import (
    MissingNotionAPITokenError,
    NotionConfigurationError,
)


def _make_env(**values: str) -> Mapping[str, str]:
    return {k: v for k, v in values.items() if v is not None}


def test_from_env_success() -> None:
    env = _make_env(
        NOTION_API_TOKEN_ENV_VAR="secret-token",
        NOTION_DEFAULT_PARENT_PAGE_ID_ENV_VAR="parent123",
    )
    settings = NotionClientSettings.from_env(env)
    assert settings.api_token == "secret-token"
    assert settings.default_parent_page_id == "parent123"


def test_from_env_missing_token_raises() -> None:
    env = _make_env()
    with pytest.raises(MissingNotionAPITokenError):
        NotionClientSettings.from_env(env)


def test_resolve_prefers_explicit_values() -> None:
    env = _make_env(NOTION_API_TOKEN_ENV_VAR="env-token")
    initial = NotionClientSettings(api_token="base-token")
    resolved = NotionClientSettings.resolve(
        api_token="override-token",
        default_parent_page_id="override-parent",
        settings=initial,
        env=env,
    )
    assert resolved.api_token == "override-token"
    assert resolved.default_parent_page_id == "override-parent"


def test_resolve_uses_env_when_settings_missing() -> None:
    env = _make_env(
        NOTION_API_TOKEN_ENV_VAR="env-token",
        NOTION_DEFAULT_PARENT_PAGE_ID_ENV_VAR="env-parent",
    )
    resolved = NotionClientSettings.resolve(env=env)
    assert resolved.api_token == "env-token"
    assert resolved.default_parent_page_id == "env-parent"


def test_require_parent_errors_without_value() -> None:
    settings = NotionClientSettings(api_token="token")
    with pytest.raises(NotionConfigurationError):
        settings.require_parent()


def test_require_parent_returns_value() -> None:
    settings = NotionClientSettings(
        api_token="token",
        default_parent_page_id="parent",
    )
    assert settings.require_parent() == "parent"


def test_redact_token_behaviour() -> None:
    assert redact_token("  secret ") == "**cret"
    assert redact_token("abcd") == "****"
    assert redact_token("a") == "*"
    assert redact_token(" ") == ""
