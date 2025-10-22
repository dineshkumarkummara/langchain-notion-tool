"""Factory helpers to construct Notion clients."""

from __future__ import annotations

import logging
import inspect
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, NamedTuple, Optional

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

    client: Client
    async_client: AsyncClient


def _load_client_classes() -> tuple[type[Client], type[AsyncClient]]:
    try:
        from notion_client import AsyncClient, Client
    except ImportError as exc:  # pragma: no cover - exercised via tests
        raise NotionConfigurationError(
            "The 'notion-client' package is required to use langchain-notion-tools."
        ) from exc
    return Client, AsyncClient


def _resolve_settings(
    *,
    api_token: Optional[str],
    default_parent_page_id: Optional[str],
    settings: Optional[NotionClientSettings],
    env: Optional[Mapping[str, str]],
) -> NotionClientSettings:
    return NotionClientSettings.resolve(
        api_token=api_token,
        default_parent_page_id=default_parent_page_id,
        settings=settings,
        env=env,
    )


def create_sync_client(
    *,
    api_token: Optional[str] = None,
    default_parent_page_id: Optional[str] = None,
    settings: Optional[NotionClientSettings] = None,
    client: Optional[Client] = None,
    env: Optional[Mapping[str, str]] = None,
    **client_kwargs: Any,
) -> Client:
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
    client_cls, _ = _load_client_classes()

    logger.debug(
        "Creating Notion sync client",
        extra={"notion_token": redact_token(token)},
    )
    init_params = inspect.signature(client_cls.__init__).parameters
    timeout_ms = int(resolved_settings.client_timeout * 1000)
    if "options" in init_params:
        # notion-client >=2.5.0 expects top-level kwargs (auth, timeout_ms, ...)
        return client_cls(
            auth=token,
            timeout_ms=timeout_ms,
            **client_kwargs,
        )

    # notion-client <2.5.0 expects `client_options`.
    client_options = dict(client_kwargs.pop("client_options", {}))
    client_options.setdefault("timeout", resolved_settings.client_timeout)
    client_options.setdefault("max_retries", resolved_settings.max_retries)
    return client_cls(auth=token, client_options=client_options, **client_kwargs)


def create_async_client(
    *,
    api_token: Optional[str] = None,
    default_parent_page_id: Optional[str] = None,
    settings: Optional[NotionClientSettings] = None,
    async_client: Optional[AsyncClient] = None,
    env: Optional[Mapping[str, str]] = None,
    **client_kwargs: Any,
) -> AsyncClient:
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
    _, async_client_cls = _load_client_classes()

    logger.debug(
        "Creating Notion async client",
        extra={"notion_token": redact_token(token)},
    )
    init_params = inspect.signature(async_client_cls.__init__).parameters
    timeout_ms = int(resolved_settings.client_timeout * 1000)
    if "options" in init_params:
        return async_client_cls(
            auth=token,
            timeout_ms=timeout_ms,
            **client_kwargs,
        )

    client_options = dict(client_kwargs.pop("client_options", {}))
    client_options.setdefault("timeout", resolved_settings.client_timeout)
    client_options.setdefault("max_retries", resolved_settings.max_retries)
    return async_client_cls(auth=token, client_options=client_options, **client_kwargs)


def create_client_bundle(
    *,
    api_token: Optional[str] = None,
    default_parent_page_id: Optional[str] = None,
    settings: Optional[NotionClientSettings] = None,
    client: Optional[Client] = None,
    async_client: Optional[AsyncClient] = None,
    env: Optional[Mapping[str, str]] = None,
    client_kwargs: Optional[Mapping[str, Any]] = None,
    async_client_kwargs: Optional[Mapping[str, Any]] = None,
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
