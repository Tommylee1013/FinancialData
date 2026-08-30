from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_KEY_FILE = PROJECT_ROOT / "config" / "api.key"
DEFAULT_CHAT_DB = PROJECT_ROOT / "database" / "findash_chat.sqlite3"
DEFAULT_FINANCE_DB = PROJECT_ROOT / "database" / "alternative_data.duckdb"


def load_openai_api_key() -> str | None:
    """Load the key without ever logging or returning it to the frontend."""
    if key := os.environ.get("OPENAI_API_KEY"):
        return key.strip()
    key_file = Path(os.environ.get("FINDASH_API_KEY_FILE", DEFAULT_KEY_FILE))
    if not key_file.is_file():
        return None
    for line in key_file.read_text(encoding="utf-8").splitlines():
        candidate = line.strip()
        if candidate.startswith("sk-"):
            return candidate
    return None


def agent_model() -> str:
    return os.environ.get("FINDASH_AGENT_MODEL", "gpt-4.1-mini")
