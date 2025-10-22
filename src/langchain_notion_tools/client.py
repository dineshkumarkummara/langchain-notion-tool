"""Factory helpers to construct Notion clients."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Mapping, NamedTuple, Tuple, Type

from .config import NotionClientSettings, redact_token
from .exceptions import NotionConfigurationError

__all__ = [
    "NotionClientBundle",
    "create_sync_client",
    "create_async_client",
    "create_client_bundle",
]

logger = logging.getLogger(__name__)

if TYPE_CHECKING:  # pragma: no cover - import for static analysis only
    from notion_client import AsyncClient, Client


class NotionClientBundle(NamedTuple):
    """Container for paired sync and async Notion clients."""

    client: "Client"
    async_client: "AsyncClient"


def _load_client_classes() -> Tuple[Type["Client"], Type["AsyncClient"]]:
    try:
        from notion_client import AsyncClient, Client
    except ImportError as exc:  # pragma: no cover - exercised via tests
        raise NotionConfigurationError(
            "The 'notion-client' package is required to use langchain-notion-tools."
        ) from exc
    return Client, AsyncClient


def _resolve_settings(
    *,
    api_token: str | None,
    default_parent_page_id: str | None,
    settings: NotionClientSettings | None,
    env: Mapping[str, str] | None,
) -> NotionClientSettings:
    return NotionClientSettings.resolve(
        api_token=api_token,
        default_parent_page_id=default_parent_page_id,
        settings=settings,
        env=env,
    )


def create_sync_client(
    *,
    api_token: str | None = None,
    default_parent_page_id: str | None = None,
    settings: NotionClientSettings | None = None,
    client: "Client" | None = None,
    env: Mapping[str, str] | None = None,
    **client_kwargs: Any,
) -> "Client":
    """Create or return a configured synchronous Notion client."""

    if client is not None:
        return client

    resolved_settings = _resolve_settings(
        api_token=api_token,
        default_parent_page_id=default_parent_page_id,
        settings=settings,
        env=env,
    )
    token = resolved_settings.api_token
    Client, _ = _load_client_classes()
    client_options = dict(client_kwargs.pop("client_options", {}))
    client_options.setdefault("timeout", resolved_settings.client_timeout)
    client_options.setdefault("max_retries", resolved_settings.max_retries)
    logger.debug(
        "Creating Notion sync client",
        extra={"notion_token": redact_token(token)},
    )
    return Client(auth=token, client_options=client_options, **client_kwargs)


def create_async_client(
    *,
    api_token: str | None = None,
    default_parent_page_id: str | None = None,
    settings: NotionClientSettings | None = None,
    async_client: "AsyncClient" | None = None,
    env: Mapping[str, str] | None = None,
    **client_kwargs: Any,
) -> "AsyncClient":
    """Create or return a configured asynchronous Notion client."""

    if async_client is not None:
        return async_client

    resolved_settings = _resolve_settings(
        api_token=api_token,
        default_parent_page_id=default_parent_page_id,
        settings=settings,
        env=env,
    )
    token = resolved_settings.api_token
    _, AsyncClient = _load_client_classes()
    client_options = dict(client_kwargs.pop("client_options", {}))
    client_options.setdefault("timeout", resolved_settings.client_timeout)
    client_options.setdefault("max_retries", resolved_settings.max_retries)
    logger.debug(
        "Creating Notion async client",
        extra={"notion_token": redact_token(token)},
    )
    return AsyncClient(auth=token, client_options=client_options, **client_kwargs)


def create_client_bundle(
    *,
    api_token: str | None = None,
    default_parent_page_id: str | None = None,
    settings: NotionClientSettings | None = None,
    client: "Client" | None = None,
    async_client: "AsyncClient" | None = None,
    env: Mapping[str, str] | None = None,
    client_kwargs: Mapping[str, Any] | None = None,
    async_client_kwargs: Mapping[str, Any] | None = None,
) -> NotionClientBundle:
    """Create both sync and async Notion clients with shared configuration."""

    resolved_settings = _resolve_settings(
        api_token=api_token,
        default_parent_page_id=default_parent_page_id,
        settings=settings,
        env=env,
    )

    sync_client = create_sync_client(
        settings=resolved_settings,
        client=client,
        **dict(client_kwargs or {}),
    )
    async_client_instance = create_async_client(
        settings=resolved_settings,
        async_client=async_client,
        **dict(async_client_kwargs or {}),
    )
    return NotionClientBundle(sync_client, async_client_instance)
