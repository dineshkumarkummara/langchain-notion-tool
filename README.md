# LangChain Notion Tools

[![CI](https://github.com/dineshkumarkummara/langchain-notion-tool/actions/workflows/ci.yml/badge.svg)](https://github.com/dineshkumarkummara/langchain-notion-tool/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen.svg)](#tests)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-mkdocs--material-2962ff.svg)](docs/index.md)

LangChain Notion Tools is an external integration package that gives LangChain agents **read and
write** access to Notion via the official Notion API. It ships a polished developer experience:

- 🔍 `NotionSearchTool` for locating pages and databases with LLM-friendly output.
- ✍️ `NotionWriteTool` for creating and updating pages with rich blocks, property updates, and
  dry-run previews.
- 🧱 Block helper utilities and a Markdown-to-Notion converter (`from_text`) to keep prompts terse.
- 🛠️ A tiny CLI (`notion-search`, `notion-write`) to debug flows without leaving the terminal.
- 📚 MkDocs-based documentation with doctested examples and JSON schemas ready for tool-calling LLMs.

> **Status:** Actively developed. Contributions and feedback are welcome!

---

## Installation

```
pip install langchain-notion-tools
```

Developers can install with extras for linting, typing, and doctests:

```
pip install -e .[dev]
```

---

## Supported block helpers

| Helper | Block type | Description |
| --- | --- | --- |
| `paragraph(text)` | `paragraph` | Standard rich-text paragraph |
| `heading_1/2/3(text)` | `heading_1/2/3` | Headings with descending emphasis |
| `bulleted_list_item(text)` | `bulleted_list_item` | Bulleted list entries |
| `numbered_list_item(text)` | `numbered_list_item` | Ordered list entries |
| `to_do(text, checked=False)` | `to_do` | Task items with optional checkbox |
| `toggle(text, children=None)` | `toggle` | Collapsible toggles with nested blocks |
| `callout(text, icon=None)` | `callout` | Callouts with optional icon metadata |
| `quote(text)` | `quote` | Quoted text blocks |
| `code(text, language="plain text")` | `code` | Code fences with link stripping |

Use `sanitize_blocks` to enforce allowlists and size limits before sending content to Notion. The
`from_text` helper converts a Markdown-like syntax (`#`, `-`, `1.`, ``` fences) into a safe block
payload.

---

## Quickstart

```python
from langchain_notion_tools import NotionSearchTool, NotionWriteTool, from_text

search = NotionSearchTool()
write = NotionWriteTool()

results = search.run(query="product roadmap")
print(results[0]["title"], results[0]["url"])

summary_blocks = from_text("### Summary\n- Release is on track\n- Risks reviewed")
response = write.run(
    update={"page_id": results[0]["id"], "mode": "append"},
    blocks=summary_blocks,
)
print(response["summary"])
```

Credentials are read from `NOTION_API_TOKEN` (and optionally `NOTION_DEFAULT_PARENT_PAGE_ID`). See
[docs/quickstart.md](docs/quickstart.md) for full setup instructions, including CLI usage.

---

## Toolkit helper

When you need both tools side by side, use the `NotionToolkit` factory. It shares a single Notion client across the search and write tools so rate limits and retries are coordinated.

```python
from langchain_notion_tools import create_toolkit

notion = create_toolkit()
for tool in notion.tools:
    print(tool.name)

# Plug into an agent
from langchain_core.runnables import RunnableParallel
workflow = RunnableParallel({"search": notion.search, "write": notion.write})
```

Call `create_toolkit(api_token="...")` to override credentials or pass an existing `NotionClientSettings` instance.

---

## CLI

Debug workflows without writing a script:

```
# Search for specs
notion-search --query "api spec" --limit 5

# Append Markdown-converted blocks to a page
notion-write --update-page "abcd1234" --blocks-from-text "### Decisions\n- Adopt OAuth2"

# Create a page in the default parent and dry-run the payload
notion-write --title "Weekly Review" --blocks-from-text "# Intro" --dry-run
```

The CLI respects the same environment variables as the Python API and prints JSON responses that
can be piped into `jq` for terminal-friendly inspection.

---

## Documentation

The full documentation (Quickstart, Configuration, Examples, JSON Schema) lives under `docs/` and
is built with MkDocs Material:

```
pip install -e .[dev] mkdocs-material
mkdocs serve
```

Open <http://127.0.0.1:8000> to browse the live docs with hot reload.

---

## Examples

The `examples/` directory contains runnable scripts and notebooks. They load `.env` files for
 convenience and show how to orchestrate read/write cycles, LangChain agents, and CLI automation.

---

## Contributing

We follow [Conventional Commits](https://www.conventionalcommits.org/), run `ruff`, `mypy`, and
`pytest` in CI, and welcome issues or pull requests. See [CONTRIBUTING.md](CONTRIBUTING.md) for the
full guide.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
