"""Append-only audit trail in SQLite (data/audit.db).

Every agent/human decision is one immutable row: what happened, when, who (agent or
human), with the reasoning/detail attached. Rows are only ever inserted, never updated
or deleted - that immutability is the point of an audit trail. This is the
accountability layer, and the data source the dashboard reads from.
"""
from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DB = Path(__file__).resolve().parents[1] / "data" / "audit.db"


def _conn() -> sqlite3.Connection:
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS audit_events (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            ts         TEXT NOT NULL,
            email_id   TEXT NOT NULL,
            event      TEXT NOT NULL,
            actor      TEXT NOT NULL,        -- 'agent' or 'human'
            category   TEXT,
            confidence REAL,
            detail     TEXT
        )
    """)
    return con


def record(email_id: str, event: str, actor: str,
           category: Optional[str] = None, confidence: Optional[float] = None,
           detail: str = "") -> None:
    con = _conn()
    con.execute(
        "INSERT INTO audit_events(ts,email_id,event,actor,category,confidence,detail) "
        "VALUES (?,?,?,?,?,?,?)",
        (datetime.now(timezone.utc).isoformat(), email_id, event, actor,
         category, confidence, detail),
    )
    con.commit()
    con.close()


def events_for(email_id: str) -> list[tuple]:
    con = _conn()
    rows = con.execute(
        "SELECT ts,event,actor,category,confidence,detail FROM audit_events "
        "WHERE email_id=? ORDER BY id", (email_id,)).fetchall()
    con.close()
    return rows


def all_email_ids() -> list[str]:
    con = _conn()
    rows = [r[0] for r in con.execute(
        "SELECT DISTINCT email_id FROM audit_events ORDER BY email_id").fetchall()]
    con.close()
    return rows


def summary() -> dict:
    con = _conn()
    rows = con.execute("SELECT event, COUNT(*) FROM audit_events GROUP BY event").fetchall()
    con.close()
    return dict(rows)
