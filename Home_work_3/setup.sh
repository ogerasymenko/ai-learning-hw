#!/usr/bin/env bash
# Environment setup for the LangGraph workshop. Run: bash setup.sh
set -euo pipefail
cd "$(dirname "$0")"

PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  echo "❌ Python 3.10+ is required. On a Mac: brew install python@3.12  (or: brew install uv)"
  exit 1
fi
echo "→ Python: $($PY --version)"

if command -v uv >/dev/null 2>&1; then
  echo "→ Installing with uv"
  uv venv -p "$PY" .venv
  uv pip install -p .venv/bin/python -r requirements.txt
else
  echo "→ Installing with pip"
  "$PY" -m venv .venv
  .venv/bin/python -m pip install -q --upgrade pip
  .venv/bin/python -m pip install -r requirements.txt
fi

if [ ! -f .env ]; then
  cp .env.example .env
  echo "→ Created .env — put your API key there"
fi

echo
echo "✅ Done. Next:"
echo "   source .venv/bin/activate"
echo "   python demos/01_state_and_edges.py   # works without a key"
echo "   python 00_sanity_check.py            # checks the key and a tool call"
