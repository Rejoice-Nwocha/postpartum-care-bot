"""Lightweight conversational memory for Care Sister.

The database message log is the source of truth. This module turns recent
messages into compact context without introducing an external AI dependency.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.db import MessageLog


@dataclass(frozen=True)
class RecentMessage:
    direction: str
    text: str


def _clean_body(body: str) -> str:
    value = (body or "").strip()
    if value.startswith("[evolution:") and "] " in value:
        value = value.split("] ", 1)[1]
    return value


def recent_messages(db: Session, wa_id: str, limit: int = 8) -> list[RecentMessage]:
    """Return recent inbound/outbound messages in chronological order."""
    rows = (
        db.query(MessageLog)
        .filter(MessageLog.wa_id == wa_id)
        .order_by(MessageLog.id.desc())
        .limit(max(1, min(limit, 20)))
        .all()
    )
    return [
        RecentMessage(row.direction, _clean_body(row.body))
        for row in reversed(rows)
        if _clean_body(row.body)
    ]


def compact_context(db: Session, wa_id: str, limit: int = 8) -> str:
    """Build a short context block suitable for deterministic conversation logic."""
    messages = recent_messages(db, wa_id, limit=limit)
    return "\n".join(
        f"{'Mother' if item.direction == 'in' else 'Care Sister'}: {item.text}"
        for item in messages
    )
