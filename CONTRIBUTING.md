# Contributing

Thank you for your interest in contributing to **langchain-notion-tools**!

## Development environment

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -e .[dev]
   ```
3. Run checks before opening a pull request:
   ```bash
   ruff check .
   mypy src
   pytest
   ```

## Commit messages

We follow [Conventional Commits](https://www.conventionalcommits.org/) to enable semantic-release automation.

## Code style

- Python 3.9+
- Type hints required
- Keep functions small and focused

## Pull requests

- Include tests for new or changed behavior
- Update documentation when you change public APIs
- Ensure CI is green before requesting review

## Reporting issues

Use the issue templates to provide as much detail as possible.
