"""Day 5 check: resolve each sample email's sender against the directory.
DONE WHEN: known senders return full records (Rita shows account=locked),
and an unknown address returns None.

Run from the repo root:  python scripts/lookup_demo.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from servicedesk.ingest import load_emails
from servicedesk.tools.directory import lookup_user


def main():
    print("Resolving senders from sample_emails.json:\n")
    for email in load_emails():
        rec = lookup_user(email.sender)
        if rec:
            print(f"{email.sender:<38} -> {rec['name']}, {rec['department']}, "
                  f"{rec['device']}, account={rec['account_status']}, mgr={rec['manager']}")
        else:
            print(f"{email.sender:<38} -> NOT FOUND")

    print("\nLookup by employee_id (4471):", lookup_user("4471"))
    print("Lookup unknown address:      ", lookup_user("ghost@northwind.example"))


if __name__ == "__main__":
    main()
