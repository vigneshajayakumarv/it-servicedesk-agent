"""Where emails come from: JSON fixtures for the demo; swap in Microsoft Graph for production.
Malformed records are skipped with a warning so one bad row can't kill a batch."""
from __future__ import annotations
import json
from pathlib import Path
from .schema import IncomingEmail

DATA = Path(__file__).resolve().parent.parent / "data" / "sample_emails.json"


def load_emails(path: str | None = None) -> list[IncomingEmail]:
    p = Path(path) if path else DATA
    raw = json.loads(p.read_text())
    emails = []
    for item in raw:
        try:
            emails.append(IncomingEmail(**item))
        except Exception as e:
            rid = item.get("id", "?") if isinstance(item, dict) else "?"
            print(f"[ingest] skipped malformed record {rid}: {e}")
    return emails
