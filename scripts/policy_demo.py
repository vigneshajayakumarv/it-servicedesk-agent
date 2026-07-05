"""Day 6 check: build the policy index, then run a few queries through the RAG tool.
DONE WHEN: build reports N chunks, and each query returns a relevant policy snippet.

Run from the repo root:  python scripts/policy_demo.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from servicedesk.tools.policy import build_index, check_policy
from servicedesk.embeddings import backend_name

QUERIES = [
    "How do I unlock a user whose account is locked after failed logins?",
    "Does a contractor need manager approval to get software access?",
    "Someone can I just be made an admin on the billing system?",
    "An employee emailed a salary spreadsheet to the wrong people. What now?",
    "How quickly must we disable a leaver's accounts?",
]

def main():
    n = build_index()
    print(f"Indexed {n} policy chunks using {backend_name()}\n")
    for q in QUERIES:
        print("Q:", q)
        print(check_policy(q))
        print()

if __name__ == "__main__":
    main()
