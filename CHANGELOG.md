# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- GitHub Actions workflow for linting, typing, testing, and building distributions.
- Issue and pull request templates plus a project Code of Conduct for contributors.
- MkDocs Material documentation site (overview, quickstart, examples, API reference, contributing) with GitHub Pages deployment.
- Expanded automated test suite covering CLI paths, Notion client helpers, and error flows to keep runtime coverage above 90%.
- `setup.cfg` packaging metadata aligning classifiers and author details with PyPI norms.

### Changed
- Applied explicit MIT license headers across all Python sources and tests.
- Refreshed README badges with PyPI coverage and linked to the LangChain docs.
- README now references the published documentation site.
- Project classified as Alpha in packaging metadata.

## [0.1.0] - 2025-10-22

### Added
- LangChain search and write tools backed by shared Notion client configuration.
- Block helper utilities, Markdown conversion, and CLI debugging commands.
- Project documentation site, runnable examples, and LangChain docs patch assets.

### Changed
- Scaffolded project tooling (ruff, mypy, pytest, CI, semantic-release).
