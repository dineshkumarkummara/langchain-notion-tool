# Configuration

LangChain Notion Tools reads configuration from environment variables, keyword arguments, or a
pre-built `NotionClientSettings` instance. This page summarizes the available options.

## Required variables

| Environment variable | Description |
| --- | --- |
| `NOTION_API_TOKEN` | Required integration token for all operations. |

## Optional variables

| Environment variable | Description |
| --- | --- |
| `NOTION_DEFAULT_PARENT_PAGE_ID` | Default page or database where new pages should be created when no explicit parent is supplied. |
| `NOTION_API_TIMEOUT` | Optional override for HTTP timeout (seconds). Defaults to `30`. |
| `NOTION_API_MAX_RETRIES` | Optional override for retry attempts on transient failures. Defaults to `3`. |

Settings are validated using [Pydantic](https://docs.pydantic.dev) and invalid values trigger
`NotionConfigurationError` with actionable hints.

## HTTP settings

The underlying Notion SDK uses `httpx`. You can pass custom client options through the
`client_kwargs`/`async_client_kwargs` parameters of `create_client_bundle`, `create_sync_client`,
or `create_async_client` if you need to tweak retry or timeout behaviour.

```python
from langchain_notion_tools import create_client_bundle

clients = create_client_bundle(
    api_token="...",
    client_kwargs={"timeout": 15},
    async_client_kwargs={"timeout": 30},
)
```

## Logging

The package uses the standard library `logging` module. Tokens are redacted by default. Enable
verbose logging when troubleshooting:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

## CLI configuration

The CLI commands (`notion-search` and `notion-write`) respect the same environment variables. A
`.env` file is loaded automatically when you run the examples in the `examples/` folder.
