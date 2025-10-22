# Contributing Guide

We welcome improvements, bug fixes, and new block helpers. This guide covers the
basics for extending the toolkit and shipping high-quality pull requests.

## Development environment

1. Fork the repository and clone it locally.
2. Install the project in editable mode with the development extras:

   ```bash
   pip install -e .[dev]
   ```

3. Run the quality checks before opening a pull request:

   ```bash
   ruff check .
   mypy --config-file mypy.ini src
   pytest
   ```

MkDocs-powered documentation lives in `docs/`. Use `mkdocs serve` for live
rendering while editing.

## Adding or extending blocks

- New helpers belong in `src/langchain_notion_tools/blocks.py`. Keep the public
  API ergonomic, mirroring Notion's block metadata.
- Validate payloads with `sanitize_blocks` to enforce block allowlists, maximum
  block counts, and total text length limits.
- Add unit tests covering success paths, failure scenarios, and serialization
  behaviour in `tests/test_blocks.py`.
- Document the helper with docstrings and update `docs/api_reference.md` if the
  helper should appear in the API reference.
- Refresh examples if the new helper unlocks a notable workflow (see
  `docs/examples.md`).

## Extending tools or the client bundle

- Implement changes in the relevant module (`tools/`, `client.py`, `config.py`),
  keeping docstrings up to date.
- Write tests under `tests/tools/` or `tests/` that exercise new behaviour. Use
  the existing fixtures for synchronous and asynchronous clients when possible.
- When updating request or response payloads, update the JSON schemas that power
  agent integrations.

## Pull request checklist

- [ ] Lints, type checks, and tests all pass locally.
- [ ] Documentation, changelog, and examples reflect the change.
- [ ] Commits follow [Conventional Commits](https://www.conventionalcommits.org/)
      and PRs include a summary plus testing notes.
- [ ] Sensitive values (tokens, database IDs) are anonymised in examples and
      fixtures.
