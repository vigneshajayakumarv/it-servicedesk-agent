"""Operational metrics from the append-only audit table (+ pending queue).

These are LIVE numbers: what the agent actually did. Model-quality/accuracy is a
separate concern (scripts/eval_dataset.py) measured on the held-out labeled set - it
is never mixed into these operational figures.
"""
from __future__ import annotations
from . import audit, queue_index

# Assumed human handling time per ticket the agent fully automated (no human touch).
MINUTES_SAVED_PER_AUTO_TICKET = 8


def operational() -> dict:
    ids = audit.all_email_ids()
    auto = approved = rejected = escalated = 0
    for eid in ids:
        types = [e[1] for e in audit.events_for(eid)]
        if "escalated" in types:
            escalated += 1
        for _ts, event, _actor, _cat, _conf, detail in audit.events_for(eid):
            if event == "resolved":
                if "path=auto" in (detail or ""):
                    auto += 1
                elif "path=approved" in (detail or ""):
                    approved += 1
            elif event == "rejected":
                rejected += 1

    processed = len(ids)
    return {
        "processed": processed,
        "auto_resolved": auto,
        "approved": approved,
        "rejected": rejected,
        "escalated": escalated,
        "pending": len(queue_index.load()),
        "auto_rate": (auto / processed) if processed else 0.0,
        "hours_saved": auto * MINUTES_SAVED_PER_AUTO_TICKET / 60,
    }
