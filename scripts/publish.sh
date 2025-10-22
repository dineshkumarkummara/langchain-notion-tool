#!/usr/bin/env bash
set -euo pipefail

if ! command -v twine >/dev/null 2>&1; then
  echo "twine is required; install with 'pip install twine'" >&2
  exit 1
fi

if [ ! -d dist ] || [ -z "$(ls -A dist 2>/dev/null)" ]; then
  echo "Building distribution artifacts..."
  python3 -m build
fi

twine upload "$@" dist/*
