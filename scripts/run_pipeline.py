"""Quick, EPHEMERAL run of the whole graph (in-memory checkpointer).
Auto items resolve; gated items PAUSE (shown, not resumable here). For the durable
queue with approve/reject that survives restarts, use scripts/inbox.py instead.

Run from the repo root:  python scripts/run_pipeline.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.checkpoint.memory import InMemorySaver
from servicedesk.ingest import load_emails
from servicedesk.agent.graph import build_graph


def main():
    graph = build_graph(InMemorySaver())
    for email in load_emails():
        print("=" * 64)
        cfg = {"configurable": {"thread_id": email.id}}
        final = graph.invoke({"email": email.model_dump(mode="json")}, cfg)
        if "__interrupt__" in final:
            print(f"PAUSED {email.id} -> awaiting approval (use scripts/inbox.py)")
        else:
            print(f"OUTCOME: {final['outcome']}")
            if final.get("draft"):
                print("--- draft ---")
                print(final["draft"])


if __name__ == "__main__":
    main()
