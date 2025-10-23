# LangChain Notion Toolkit: Automate Notion with LLMs

## Overview
The LangChain Notion Toolkit is an open-source bridge between LangChain agents and the Notion API. It lets your LLM-powered copilots search, create, and update Notion pages and databases using the official SDK—no brittle glue scripts required.

- **Search** Notion spaces for the right page or database with structured results.
- **Write** rich Notion blocks (headings, lists, callouts, code) with safe allow-lists and size limits.
- **Async + sync** support so you can drop it into any LangChain workflow.
- **CLI utilities** for debugging requests before putting an agent in the loop.

The toolkit is MIT licensed and already published on PyPI. It was recently featured in the LangChain documentation as an external integration.

## Agent example
```python
from langchain import OpenAI, initialize_agent, AgentType
from langchain_notion_tools import NotionSearchTool, NotionWriteTool

llm = OpenAI(temperature=0)
search_tool = NotionSearchTool(api_token="…", default_parent_page_id="…")
write_tool = NotionWriteTool(api_token="…", default_parent_page_id="…")

agent = initialize_agent(
    tools=[search_tool, write_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)

agent.run(
    "Find the product spec in Notion titled 'Q2 roadmap', "
    "add a new section 'Decisions made 2025-10' with bullet list …"
)
```

## Demo
![Animated Notion page update showing appended bullet list](docs/images/notion_write_example.gif)

## Links
- GitHub: https://github.com/dineshkumarkummara/langchain-notion-tool
- PyPI: https://pypi.org/project/langchain-notion-tools/
- LangChain Docs PR: https://github.com/langchain-ai/langchain/pull/33645
- Roadmap / issues: https://github.com/dineshkumarkummara/langchain-notion-tool/issues

## Tags
`#NotionAPI #LangChain #OpenSource #Python #AIagents`

Developers are welcome to extend block support, add attachment handling, or contribute async improvements—let’s build richer Notion automations together!
