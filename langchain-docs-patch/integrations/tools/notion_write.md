# Notion Write Toolkit

LangChain’s Notion write integration is delivered via the external
[`langchain-notion-tools`](https://pypi.org/project/langchain-notion-tools/) package. It exposes agent-ready tools for reading and writing Notion content—no manual REST plumbing required.

## Installation

```bash
pip install langchain-notion-tools
```

Set the Notion integration token (and optional default parent) as environment variables:

```bash
export NOTION_API_TOKEN="secret_abc123"
export NOTION_DEFAULT_PARENT_PAGE_ID="abcd1234efgh5678ijkl9012"  # optional
```

## Toolkit usage

```python
from langchain_notion_tools import create_toolkit
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent

llm = ChatOpenAI(model="gpt-4o-mini")
notion = create_toolkit()

tools = notion.tools
prompt = """You are a product operations assistant. Write an action log summarising the latest launch."""

agent = create_tool_calling_agent(llm, tools)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
executor.invoke({"input": prompt})
```

The toolkit shares a single underlying Notion client between the search and write tools, enabling coordinated retries and connection reuse.

## CLI demonstration

The package includes a CLI for quick experimentation. The following asciinema session shows a dry-run append operation before committing the change:

```{.cast include="../assets/notion-write.cast"}
```

## LangGraph example

```python
from langchain_notion_tools import create_toolkit
from langgraph.graph import StateGraph

notion = create_toolkit()

def draft(state: dict) -> dict:
    hits = notion.search.run(query=state["query"])
    return {"hits": hits}

def write(state: dict) -> dict:
    summary_blocks = notion.write.from_text("""### Decision\n- Proceed with rollout""")
    response = notion.write.run(
        update={"page_id": state["hits"][0]["id"], "mode": "append"},
        blocks=summary_blocks,
    )
    return {"notion_response": response}

graph = StateGraph(dict)
graph.add_node("draft", draft)
graph.add_node("write", write)
graph.add_edge("draft", "write")
app = graph.compile()
app.invoke({"query": "Weekly Launch Plan"})
```

## Supported block helpers

`langchain-notion-tools` includes a helper module for creating Notion-compatible blocks. Highlight the supported helpers in your prompts or use the provided `from_text` converter:

- `paragraph(text)` – paragraphs of rich text.
- `heading_1/2/3(text)` – heading blocks.
- `bulleted_list_item(text)` / `numbered_list_item(text)` – list entries.
- `to_do(text, checked=False)` – checkbox items.
- `toggle(text, children=None)` – collapsible content.
- `callout(text, icon=None)` – callouts with optional icon metadata.
- `quote(text)` – block quotes.
- `code(text, language="plain text")` – code blocks (links stripped for safety).

## Error handling

Errors from Notion’s API are mapped into `ToolExecutionError` with succinct context, and the toolkit enforces block allowlists, size limits, and safe logging by default.
