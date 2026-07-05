"""Shared pending-approval index (data/pending_index.json).

A lightweight pointer list of threads paused awaiting human approval. The full paused
state lives in the checkpoint; this is just what the CLI and dashboard list. Both read
and write it through here so the two never drift.
"""
from __future__ import annotations
import json
from pathlib import Path

INDEX = Path(__file__).resolve().parents[1] / "data" / "pending_index.json"


def load() -> dict:
    return json.loads(INDEX.read_text()) if INDEX.exists() else {}


def add(thread_id: str, info: dict) -> None:
    ix = load()
    ix[thread_id] = info
    _save(ix)


def remove(thread_id: str) -> None:
    ix = load()
    ix.pop(thread_id, None)
    _save(ix)


def _save(ix: dict) -> None:
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(json.dumps(ix, indent=2))
