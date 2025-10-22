# API Reference

This reference is generated automatically from the package docstrings using
[`mkdocstrings`](https://mkdocstrings.github.io/). Use it to explore the public
APIs exposed by the toolkit, tools, configuration helpers, and block utilities.

## Toolkit

::: langchain_notion_tools.toolkit
    options:
      members:
        - NotionToolkit
        - create_toolkit

## Tools

::: langchain_notion_tools.tools.search
    options:
      members:
        - NotionSearchTool

::: langchain_notion_tools.tools.write
    options:
      members:
        - NotionWriteTool

## Clients

::: langchain_notion_tools.client
    options:
      members:
        - NotionClientBundle
        - create_client_bundle
        - create_sync_client
        - create_async_client

## Configuration

::: langchain_notion_tools.config
    options:
      filters:
        - "!^_"
      members:
        - NotionClientSettings
        - NOTION_API_TOKEN_ENV_VAR
        - NOTION_DEFAULT_PARENT_PAGE_ID_ENV_VAR
        - redact_token

## Blocks

::: langchain_notion_tools.blocks
    options:
      filters:
        - "!^_"
      members:
        - ALLOWED_BLOCK_TYPES
        - MAX_BLOCKS
        - MAX_TOTAL_TEXT_LENGTH
        - bulleted_list_item
        - callout
        - code
        - from_text
        - heading_1
        - heading_2
        - heading_3
        - numbered_list_item
        - paragraph
        - quote
        - sanitize_blocks
        - to_do
        - toggle
