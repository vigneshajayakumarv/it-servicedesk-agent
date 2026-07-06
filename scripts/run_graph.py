"""Minimal graph runner: classify each sample email inside the graph and print routing.
Expected: every email is classified by the LLM inside the graph and routed to auto/human.

Run from the repo root:  python scripts/run_graph.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from servicedesk.ingest import load_emails
from servicedesk.agent.graph import build_graph


def main():
    graph = build_graph()
    for email in load_emails():
        print(f"\nINPUT: {email.id}  {email.subject!r}")
        final = graph.invoke({"email": email})
        print(f"OUTCOME: {final['outcome']}")


if __name__ == "__main__":
    main()
