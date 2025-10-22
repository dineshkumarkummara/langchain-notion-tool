# LLM-friendly JSON Schema

Both tools expose Pydantic models so you can derive machine-readable schemas for use with OpenAI
function calling, Anthropic tool use, or LangChain's structured output APIs. Generate the schema at
runtime to keep it in sync with the code:

```python
>>> import json
>>> from langchain_notion_tools.tools import NotionSearchInput, NotionWriteInput
>>> json.dumps(NotionSearchInput.model_json_schema(), indent=2)
'{
  "title": "NotionSearchInput",
  "type": "object",
  ...
}'
```

Below is a shortened excerpt of the current schemas to help you craft prompts:

```json
{
  "title": "NotionSearchInput",
  "type": "object",
  "properties": {
    "query": {"type": "string", "description": "Full-text query passed to Notion."},
    "page_id": {"type": "string", "description": "Retrieve a specific page by ID."},
    "database_id": {"type": "string", "description": "Query a database by ID."},
    "filter": {"type": "object", "additionalProperties": {}, "description": "Optional filter payload forwarded to Notion."}
  }
}
```

```json
{
  "title": "NotionWriteInput",
  "type": "object",
  "properties": {
    "title": {"type": "string", "description": "Title for the page."},
    "parent": {
      "allOf": [
        {
          "type": "object",
          "properties": {
            "page_id": {"type": "string"},
            "database_id": {"type": "string"}
          },
          "description": "Exactly one of page_id or database_id must be supplied."
        }
      ]
    },
    "blocks": {
      "type": "array",
      "items": {"type": "object"},
      "description": "List of Notion block payloads."
    },
    "update": {
      "type": "object",
      "properties": {
        "page_id": {"type": "string"},
        "mode": {"type": "string", "enum": ["append", "replace"]}
      },
      "description": "Update instructions for existing pages."
    },
    "properties": {"type": "object", "additionalProperties": {}},
    "is_dry_run": {"type": "boolean", "default": false}
  }
}
```

When prompting an LLM, supply the JSON schema via the tool definition so the model knows which
fields are required and how to format block payloads.
