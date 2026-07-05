"""Durable SQLite checkpointer. Persists paused graph state to disk so an escalated
item can be resumed later, from a different process. This is what makes the
human-in-the-loop pause survive a restart."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from langgraph.checkpoint.sqlite import SqliteSaver

DB = Path(__file__).resolve().parents[1] / "data" / "checkpoints.sqlite"


def get_checkpointer() -> SqliteSaver:
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB, check_same_thread=False)
    saver = SqliteSaver(conn)
    saver.setup()  # create the checkpoint tables if they don't exist yet
    return saver
