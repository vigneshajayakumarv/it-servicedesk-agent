"""Mock employee directory lookup, backed by SQLite (data/directory.db).

In production this is Microsoft Graph / Active Directory. The agent uses this to
enrich an email with who the sender is before deciding what to do.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Optional

DB = Path(__file__).resolve().parents[2] / "data" / "directory.db"


def lookup_user(identifier: str) -> Optional[dict]:
    """Look up an employee by email address or employee_id.

    Returns the employee record as a dict, or None if not found.
    """
    if not identifier:
        return None
    # column is chosen from a fixed set (never user input); the value is parameterized.
    field = "email" if "@" in identifier else "employee_id"
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        cur = con.execute(
            f"SELECT * FROM employees WHERE {field} = ?", (identifier.strip(),)
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        con.close()
