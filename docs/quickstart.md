# Quickstart

Follow these steps to add LangChain Notion Tools to a new or existing LangChain project.

## 1. Install the package

```bash
pip install langchain-notion-tools
```

The package depends on `langchain-core`, `notion-client`, `httpx`, and `anyio`. They will be
installed automatically.

## 2. Configure credentials

Create an integration inside Notion and copy the internal integration token. Export it in your
shell (or use your preferred secret manager):

```bash
export NOTION_API_TOKEN="secret_abc123"
```

Optionally define a default parent page or database that new pages should inherit:

```bash
export NOTION_DEFAULT_PARENT_PAGE_ID="abcd1234efgh5678ijkl9012"
```

Tokens are redacted in logs and are never written to disk.

## 3. Use the tools in LangChain

```python
from langchain_core.runnables import RunnableParallel
from langchain_notion_tools import NotionSearchTool, NotionWriteTool

search = NotionSearchTool()
write = NotionWriteTool()

workflow = RunnableParallel({
    "prior_art": search.bind(query="product roadmap"),
    "create": write.bind(
        parent={"page_id": "abcd1234efgh5678ijkl9012"},
        title="LLM roadmap review",
        blocks=[
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Draft body"}}]},
            }
        ],
        is_dry_run=True,
    ),
})
result = workflow.invoke({})
print(result["create"]["summary"])
```

The tools are standard LangChain runnables. Bind arguments for reuse or call them directly inside
custom agents.

## 4. Use the toolkit

Prefer a bundled setup? The `NotionToolkit` factory wires both tools to the same underlying
Notion clients, enabling shared retry policy and reduced connection overhead:

```python
from langchain_notion_tools import create_toolkit

notion = create_toolkit()
agent = RunnableParallel({"search": notion.search, "write": notion.write})
```

## 5. Debug with the CLI

Two helper commands are installed automatically:

```bash
# Search for OKRs
notion-search --query "company okr"

# Append blocks created from Markdown to an existing page
notion-write --update-page "abcd1234" --blocks-from-text "### Action Items\n- Ship release"
```

The CLI is invaluable when iterating on prompts or testing block conversions before handing
control to an agent.
