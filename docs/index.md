# LangChain Notion Tools

LangChain Notion Tools brings first-class read and write capabilities for Notion into LangChain
agents and workflows. The package provides:

- `NotionSearchTool` – locate databases and pages with normalized results ready for LLMs.
- `NotionWriteTool` – create or update pages with rich block payloads, property updates, and
  dry-run previews.
- `NotionToolkit` – convenience factory bundling both tools with shared retry-aware clients.
- Block helper utilities, Markdown-to-Notion conversion, and a lightweight CLI for rapid
  debugging.

## Why this package

- **Agent native** – tools implement the LangChain tool protocol with sync and async runtimes.
- **Secure by design** – block allowlists, size limits, and safe token redaction are enabled by
  default.
- **LLM-friendly shape** – inputs and outputs are powered by Pydantic models with JSON schema
  tuned for structured prompting.
- **Ergonomic** – ship a CLI, docs, and runnable examples so you can iterate quickly.

> 💡 **Compatibility:** Requires Python 3.9+, `langchain-core>=0.3`, and the official
> [`notion-client`](https://github.com/ramnes/notion-sdk-py) SDK.

Explore the remainder of the docs for quickstarts, configuration tips, worked examples, and JSON
schema references suitable for LLM prompt injection.
