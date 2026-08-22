"""Small JSON-backed memory store for self-update conversations and history."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from threading import RLock
from typing import Any


logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent
CONVERSATIONS_FILE = ROOT / "conversations.json"
FACTS_FILE = ROOT / "learned_facts.json"
UPDATES_FILE = ROOT / "updates_log.json"
PENDING_FILE = ROOT / "pending_updates.json"
_lock = RLock()


def _read(path: Path, default: Any) -> Any:
    with _lock:
        try:
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Could not read memory file %s: %s", path.name, exc)
        return default


def _write(path: Path, value: Any) -> None:
    with _lock:
        ROOT.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(value, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        temporary.replace(path)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def append_conversation(
    prompt: str,
    ai_reply: dict[str, Any] | str,
    result: str,
    *,
    error: str | None = None,
) -> None:
    entries = _read(CONVERSATIONS_FILE, [])
    if not isinstance(entries, list):
        entries = []
    entries.append(
        {
            "timestamp": _now(),
            "prompt": prompt,
            "ai_reply": ai_reply,
            "result": result,
            "error": error,
        }
    )
    _write(CONVERSATIONS_FILE, entries[-200:])


def recent_conversations(limit: int = 5) -> list[dict[str, Any]]:
    entries = _read(CONVERSATIONS_FILE, [])
    return entries[-limit:] if isinstance(entries, list) else []


def update_learned_facts(facts: dict[str, Any] | None) -> None:
    if not facts:
        return
    existing = _read(FACTS_FILE, {})
    if not isinstance(existing, dict):
        existing = {}
    for key, value in facts.items():
        if key and value is not None:
            existing[str(key)] = value
    _write(FACTS_FILE, existing)


def derive_project_facts(context_files: dict[str, str]) -> dict[str, Any]:
    """Derive stable project facts from the source snapshot without secrets."""
    paths = set(context_files)
    facts: dict[str, Any] = {}

    if "telegram_userbot/main.py" in paths:
        facts["entry_file"] = "telegram_userbot/main.py"

    frameworks: list[str] = []
    combined = "\n".join(context_files.values())
    if "telethon" in combined:
        frameworks.append("Telethon")
    if "telegram.ext" in combined or "python-telegram-bot" in combined:
        frameworks.append("python-telegram-bot")
    if frameworks:
        facts["framework"] = ", ".join(frameworks)

    if "telegram_userbot/plugin_loader.py" in paths:
        facts["plugin_pattern"] = "telegram_userbot/plugins/*.py loaded per hosted Telethon client"

    storage_files = sorted(
        path
        for path in paths
        if path.startswith("telegram_userbot/DB/")
        or path.startswith("telegram_userbot/database/")
        or path.startswith("database/")
    )
    storage_files.extend(
        path
        for path in (
            "memory/conversations.json",
            "memory/learned_facts.json",
            "memory/updates_log.json",
            "memory/pending_updates.json",
            "memory/keys_state.json",
        )
        if (ROOT.parent / path).exists()
    )
    if storage_files:
        facts["storage_files"] = sorted(set(storage_files))

    return facts


def learned_facts() -> dict[str, Any]:
    facts = _read(FACTS_FILE, {})
    return facts if isinstance(facts, dict) else {}


def recent_updates(limit: int = 3) -> list[dict[str, Any]]:
    entries = _read(UPDATES_FILE, [])
    return entries[-limit:] if isinstance(entries, list) else []


def record_update(
    *,
    prompt: str,
    summary: str,
    changed_files: list[str],
    provider: str | None,
    backup_timestamp: str,
    result: str = "success",
    provider_calls: list[dict[str, Any]] | None = None,
) -> None:
    entries = _read(UPDATES_FILE, [])
    if not isinstance(entries, list):
        entries = []
    entries.append(
        {
            "timestamp": _now(),
            "prompt_summary": prompt[:240],
            "summary": summary[:500],
            "changed_files": changed_files,
            "provider": provider,
            "backup_timestamp": backup_timestamp,
            "result": result,
            "provider_calls": provider_calls or [],
        }
    )
    _write(UPDATES_FILE, entries[-200:])


def queue_pending_update(
    *,
    prompt: str,
    context_files: dict[str, str],
    sender_id: int | None = None,
    provider: str | None = None,
) -> str:
    pending = _read(PENDING_FILE, [])
    if not isinstance(pending, list):
        pending = []
    item_id = f"{int(time.time())}-{len(pending) + 1}"
    pending.append(
        {
            "id": item_id,
            "queued_at": _now(),
            "prompt": prompt,
            "context_files": context_files,
            "sender_id": sender_id,
            "provider": provider,
        }
    )
    _write(PENDING_FILE, pending[-100:])
    return item_id


def pending_updates() -> list[dict[str, Any]]:
    pending = _read(PENDING_FILE, [])
    return pending if isinstance(pending, list) else []


def remove_pending_update(item_id: str) -> None:
    pending = [item for item in pending_updates() if item.get("id") != item_id]
    _write(PENDING_FILE, pending)


def memory_stats(provider_summary: dict[str, Any] | None = None) -> dict[str, Any]:
    conversations = _read(CONVERSATIONS_FILE, [])
    updates = _read(UPDATES_FILE, [])
    pending = _read(PENDING_FILE, [])
    last_update = updates[-1] if isinstance(updates, list) and updates else None
    return {
        "conversations": len(conversations) if isinstance(conversations, list) else 0,
        "updates": len(updates) if isinstance(updates, list) else 0,
        "pending": len(pending) if isinstance(pending, list) else 0,
        "last_update": last_update.get("timestamp") if isinstance(last_update, dict) else None,
        "last_provider": last_update.get("provider") if isinstance(last_update, dict) else None,
        "providers": provider_summary or {},
    }
