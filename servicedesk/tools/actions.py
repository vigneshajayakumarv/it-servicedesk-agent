"""Side-effecting actions: real artifacts, stubbed last mile.

  draft_reply   really writes a reply (LLM), saved to data/outbox/<id>.txt
  create_ticket really records a ticket row in data/tickets.db
  escalate      really queues the item in data/pending_queue.jsonl (the HITL queue)
  reset_password SIMULATED - logs intent, changes nothing (prod: Graph/AD call)
"""
from __future__ import annotations
import json, sqlite3
from datetime import datetime, timezone
from pathlib import Path

from ..schema import IncomingEmail, Classification
from ..llm import LLMClient

_ROOT = Path(__file__).resolve().parents[2]
OUTBOX = _ROOT / "data" / "outbox"
TICKETS_DB = _ROOT / "data" / "tickets.db"
QUEUE = _ROOT / "data" / "pending_queue.jsonl"

# which team each category routes to
QUEUE_MAP = {
    "password_reset": "Identity & Access",
    "access_request": "Identity & Access",
    "onboarding_offboarding": "Identity & Access",
    "hardware": "Desktop Support",
    "vpn_network": "Network",
    "email_issue": "Messaging",
    "security_concern": "Security",
    "howto_question": "Service Desk",
    "other": "Service Desk",
}

_client = None
def _get_client() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def draft_reply(email: IncomingEmail, classification: Classification,
                user: dict | None = None, policy: str = "") -> str:
    """Write a real, grounded reply email. Saves it to the outbox and returns the body."""
    system = (
        "You are an IT service desk agent writing a reply to an employee. "
        "Reply in PLAIN TEXT only: no Markdown, no bold, no headings, no bullet symbols, "
        "and do NOT include a subject line (it is added separately). "
        "Be specific and helpful. If policy requires manager approval or a security "
        "review, say so plainly. Do not invent facts you weren't given (e.g. specific URLs). "
        "Keep it under 120 words. Sign off on a new line as 'IT Service Desk'."
    )
    context = []
    if user:
        context.append(
            f"Sender on file: {user.get('name')}, {user.get('department')}, "
            f"device {user.get('device')}, account status: {user.get('account_status')}."
        )
    if policy:
        context.append(f"Relevant policy: {policy}")
    user_msg = (
        f"Employee email:\nFrom: {email.sender}\nSubject: {email.subject}\n{email.body}\n\n"
        f"Category: {classification.category.value}\n"
        + ("\n".join(context) if context else "")
        + "\n\nWrite the reply."
    )
    body = _get_client().complete(system, user_msg)
    if not body:  # drafting failed -> safe acknowledgement so the ticket still opens
        body = ("Thank you for contacting the IT Service Desk. We've received your "
                "request and a technician will follow up shortly.\n\nIT Service Desk")
    OUTBOX.mkdir(parents=True, exist_ok=True)
    (OUTBOX / f"{email.id}.txt").write_text(
        f"To: {email.sender}\nSubject: Re: {email.subject}\n\n{body}\n"
    )
    return body


def create_ticket(email: IncomingEmail, classification: Classification) -> str:
    """Record a ticket in SQLite and return its id."""
    TICKETS_DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(TICKETS_DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id  TEXT PRIMARY KEY,
            email_id   TEXT,
            requester  TEXT,
            category   TEXT,
            queue      TEXT,
            status     TEXT,
            created_at TEXT,
            summary    TEXT
        )
    """)
    ticket_id = f"INC-{email.id.split('-')[-1]}"
    queue = QUEUE_MAP.get(classification.category.value, "Service Desk")
    con.execute(
        "INSERT OR REPLACE INTO tickets VALUES (?,?,?,?,?,?,?,?)",
        (ticket_id, email.id, email.sender, classification.category.value,
         queue, "open", _now(), email.subject),
    )
    con.commit()
    con.close()
    return ticket_id


def escalate(email: IncomingEmail, classification: Classification, reason: str) -> str:
    """Queue the item for a human. This JSONL file is the HITL approval queue (wired Day 9)."""
    entry = {
        "email_id": email.id,
        "requester": email.sender,
        "category": classification.category.value,
        "confidence": classification.confidence,
        "reason": reason,
        "status": "awaiting_approval",
        "queued_at": _now(),
    }
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    with QUEUE.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    return f"escalated {email.id} -> human queue ({reason})"


def reset_password(user_id: str) -> str:
    """SIMULATED. Logs intent but changes nothing. In production this calls Graph / AD."""
    return f"[simulated] password reset issued for {user_id} (no real change made)"
