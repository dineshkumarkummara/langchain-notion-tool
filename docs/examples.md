# Examples

End-to-end LangChain agent flow examples that you can run locally.

The snippets below run as doctests. They use in-memory stand-ins for the Notion SDK so you can
experiment without calling the live API. Swap the stub classes for real `notion-client` instances
when integrating into your project.

```python
>>> import asyncio
>>> from langchain_notion_tools.config import NotionClientSettings
>>> from langchain_notion_tools.tools import NotionSearchTool, NotionWriteTool
>>> from langchain_notion_tools.blocks import from_text
>>> class MemoryPages:
...     def __init__(self):
...         self.created = []
...         self.updated = []
...         self.retrieved = {}
...     def create(self, **payload):
...         self.created.append(payload)
...         page_id = f"page-{len(self.created)}"
...         url = f"https://notion.local/{page_id}"
...         self.retrieved[page_id] = {"id": page_id, "url": url}
...         return {"id": page_id, "url": url}
...     def update(self, *, page_id, properties):
...         self.updated.append((page_id, properties))
...         return {"id": page_id, "url": f"https://notion.local/{page_id}"}
...     def retrieve(self, *, page_id):
...         return self.retrieved.get(page_id, {"id": page_id, "url": f"https://notion.local/{page_id}"})
>>> class MemoryBlocksChildren:
...     def __init__(self):
...         self.appended = []
...     def append(self, **payload):
...         self.appended.append(payload)
...         return {"results": payload.get("children", [])}
>>> class MemoryBlocks:
...     def __init__(self):
...         self.children = MemoryBlocksChildren()
>>> class MemoryAsyncPages(MemoryPages):
...     async def create(self, **payload):
...         return super().create(**payload)
...     async def update(self, *, page_id, properties):
...         return super().update(page_id=page_id, properties=properties)
...     async def retrieve(self, *, page_id):
...         return super().retrieve(page_id=page_id)
>>> class MemoryAsyncBlocksChildren(MemoryBlocksChildren):
...     async def append(self, **payload):
...         return super().append(**payload)
>>> class MemoryAsyncBlocks:
...     def __init__(self):
...         self.children = MemoryAsyncBlocksChildren()
>>> class MemorySearch:
...     def __init__(self, results):
...         self.results = results
...         self.calls = []
...     def __call__(self, **kwargs):
...         self.calls.append(kwargs)
...         return {"results": self.results}
>>> class MemoryDatabases:
...     def __init__(self, rows):
...         self.rows = rows
...         self.calls = []
...     def query(self, *, database_id, **kwargs):
...         self.calls.append((database_id, kwargs))
...         return {"results": self.rows}
>>> class MemoryClient:
...     def __init__(self, search_results=None, database_rows=None):
...         self.pages = MemoryPages()
...         self.blocks = MemoryBlocks()
...         self.search = MemorySearch(search_results or [])
...         self.databases = MemoryDatabases(database_rows or [])
>>> class MemoryAsyncClient:
...     def __init__(self, search_results=None, database_rows=None):
...         self.pages = MemoryAsyncPages()
...         self.blocks = MemoryAsyncBlocks()
...         self.search = MemorySearch(search_results or [])
...         self.databases = MemoryDatabases(database_rows or [])
```

## 1. Create a page then append an action items section

```python
>>> sync_client = MemoryClient()
>>> async_client = MemoryAsyncClient()
>>> settings = NotionClientSettings(api_token="test-token")
>>> write_tool = NotionWriteTool(settings=settings, client=sync_client, async_client=async_client)
>>> draft_blocks = from_text("""# Weekly Review\n\n- Align roadmap\n- Confirm launch dates""")
>>> write_tool.run(title="Weekly Review", parent={"page_id": "parent-1"}, blocks=draft_blocks)["summary"]
"Created page under page parent-1 with title 'Weekly Review' and 3 block(s)."
>>> action_items = from_text("""### Action Items\n- Draft release notes\n- Schedule beta kickoff""")
>>> write_tool.run(update={"page_id": "page-1", "mode": "append"}, blocks=action_items)["summary"]
"Appended 2 block(s) on page page-1."
```

## 2. Update an existing page with a summary

```python
>>> write_tool.run(
...     update={"page_id": "page-1", "mode": "append"},
...     blocks=from_text("## Summary\n- Reached parity with v1"),
... )["summary"]
"Appended 1 block(s) on page page-1."
```

## 3. Find a spec then post a decision log

```python
>>> spec_hit = [{
...     "object": "page",
...     "id": "spec-123",
...     "url": "https://notion.local/spec-123",
...     "parent": {"type": "database_id", "database_id": "db-specs"},
...     "properties": {
...         "Title": {"type": "title", "title": [{"plain_text": "API Spec"}]},
...         "Summary": {"type": "rich_text", "rich_text": [{"plain_text": "Latest API changes"}]},
...     },
... }]
>>> sync_client.search = MemorySearch(spec_hit)
>>> async_client.search = MemorySearch(spec_hit)
>>> search_tool = NotionSearchTool(client=sync_client, async_client=async_client)
>>> search_tool.run(query="API spec")
[{'title': 'API Spec', 'object_type': 'page', 'id': 'spec-123', 'url': 'https://notion.local/spec-123', 'parent_id': 'db-specs', 'preview': 'Latest API changes'}]
>>> decision_log = from_text("""### Decision\n- Adopt OAuth2\n- Sunset legacy keys""")
>>> write_tool.run(update={"page_id": "spec-123", "mode": "append"}, blocks=decision_log)["summary"]
"Appended 2 block(s) on page spec-123."
```

## 4. Agent-style confirmation before writing to Notion

```python
>>> async def agent_flow(prompt: str) -> dict:
...     proposal = from_text(f"# Draft\n{prompt}")
...     preview = write_tool.run(
...         update={"page_id": "spec-123", "mode": "append"},
...         blocks=proposal,
...         is_dry_run=True,
...     )
...     # pretend we confirmed with the human
...     return await write_tool.arun(
...         update={"page_id": "spec-123", "mode": "append"},
...         blocks=proposal,
...     )
>>> asyncio.run(agent_flow("Summaries must call out risk items"))["summary"]
'Appended 1 block(s) on page spec-123.'
```
