# FinDash Research Agent

This package contains the backend for the FinDash AI Research workspace. It is intentionally isolated from the existing data loaders and scheduled jobs.

## Storage

- Financial data: `database/alternative_data.duckdb` (opened read-only)
- Conversation history: `database/findash_chat.sqlite3`
- API key: `OPENAI_API_KEY`, falling back to the first OpenAI-shaped key in `config/api.key`

## Configuration

- `FINDASH_AGENT_MODEL` changes the model (default: `gpt-4.1-mini`).
- `FINDASH_API_KEY_FILE` changes the fallback key-file location.

The FinDash API exposes status, conversation, message, and deletion endpoints under `/api/agent/*`. Tool calls are allowlisted in `tools.py`; the model cannot execute arbitrary SQL or modify the financial database.
