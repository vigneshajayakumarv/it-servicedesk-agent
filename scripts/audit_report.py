"""Day 10: print the full audit trail per email, plus a summary.
Run from the repo root:  python scripts/audit_report.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from servicedesk import audit


def main():
    ids = audit.all_email_ids()
    if not ids:
        print("No audit events yet. Run:  python scripts/inbox.py run")
        return
    for eid in ids:
        print(f"=== {eid} ===")
        for ts, event, actor, cat, conf, detail in audit.events_for(eid):
            t = ts[11:19]
            meta = f" {cat} ({conf:.2f})" if conf is not None else ""
            print(f"  {t}  [{actor:5}] {event:10}{meta}  {detail}")
        print()
    print("Summary:", audit.summary())


if __name__ == "__main__":
    main()
