"""Day 7 check: run sample emails through classify + the gate, then take action.
Auto items get a grounded draft + a ticket; human items get escalated.
DONE WHEN: outbox/*.txt drafts appear, tickets land in tickets.db, escalations
land in pending_queue.jsonl.

Run from the repo root:  python scripts/actions_demo.py
"""
import sys, os, json, sqlite3
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from servicedesk.ingest import load_emails
from servicedesk.llm import LLMClient
from servicedesk.hitl import needs_human
from servicedesk.tools.directory import lookup_user
from servicedesk.tools.policy import check_policy
from servicedesk.tools.actions import (
    draft_reply, create_ticket, escalate, OUTBOX, TICKETS_DB, QUEUE,
)


def main():
    client = LLMClient()
    for email in load_emails():
        c = client.classify(email)
        route = "human" if needs_human(c) else "auto"
        print("=" * 64)
        print(f"{email.id} {email.subject!r} -> {c.category.value} "
              f"({c.confidence:.2f}) [{route}]")
        if route == "human":
            print(escalate(email, c, reason=f"{c.category.value} requires approval"))
        else:
            user = lookup_user(email.sender)
            policy = check_policy(c.suggested_action or email.subject)
            draft = draft_reply(email, c, user=user, policy=policy)
            tid = create_ticket(email, c)
            print(f"ticket {tid} created; draft saved to outbox/{email.id}.txt")
            print("--- draft ---")
            print(draft)

    print("\n" + "=" * 64 + "\nSIDE EFFECTS")
    print("Outbox drafts:", sorted(p.name for p in OUTBOX.glob("*.txt")))
    con = sqlite3.connect(TICKETS_DB)
    print("Tickets:", con.execute("SELECT ticket_id, queue, status FROM tickets").fetchall())
    con.close()
    if QUEUE.exists():
        print("Pending queue:",
              [json.loads(l)["email_id"] for l in QUEUE.read_text().splitlines()])


if __name__ == "__main__":
    main()
