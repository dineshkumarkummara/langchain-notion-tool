# Examples

The scripts in this folder demonstrate end-to-end workflows. Each script loads environment
variables from a local `.env` file if present. At minimum you must export `NOTION_API_TOKEN` before
running them against the real Notion API.

## Scripts

| Script | Description |
| --- | --- |
| `create_page.py` | Convert Markdown into Notion blocks and create a new page (optionally dry-run). |
| `decision_log.py` | Search for a spec page, then append a decision log with Markdown-converted blocks. |

Run the scripts directly or explore the accompanying notebook in `examples/notebooks` for a guided
agent experience.
