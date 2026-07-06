"""Durable human-in-the-loop inbox CLI.

  python scripts/inbox.py run            process the inbox; auto-resolve safe items, PAUSE the rest
  python scripts/inbox.py queue          list items awaiting human approval
  python scripts/inbox.py approve <id>   resume a paused item as approved
  python scripts/inbox.py reject  <id>   resume a paused item as rejected

Paused state lives in data/checkpoints.sqlite. To start clean, delete that plus
data/pending_index.json, data/tickets.db, data/audit.db, and the data/outbox folder.
"""
import sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.types import Command
from servicedesk import audit, queue_index
from servicedesk.ingest import load_emails
from servicedesk.agent.graph import build_graph
from servicedesk.checkpoint import get_checkpointer


def cmd_run(args):
    graph = build_graph(get_checkpointer())
    for email in load_emails(getattr(args, 'dataset', None)):
        cfg = {"configurable": {"thread_id": email.id}}
        result = graph.invoke({"email": email.model_dump(mode="json")}, cfg)
        if "__interrupt__" in result:
            p = result["__interrupt__"][0].value
            queue_index.add(email.id, {k: p.get(k) for k in ("requester", "subject", "category", "confidence")})
            audit.record(email.id, "escalated", "agent", p.get("category"), p.get("confidence"), "awaiting human approval")
            print(f"PAUSED  {email.id}  {p.get('category')}  -> awaiting approval")
        else:
            print(f"DONE    {email.id}  {result.get('outcome')}")
    n = len(queue_index.load())
    print(f"\n{n} item(s) awaiting approval. Use:  python scripts/inbox.py queue")


def cmd_queue(_args):
    ix = queue_index.load()
    if not ix:
        print("Queue empty.")
        return
    print(f"{len(ix)} awaiting approval:\n")
    for tid, info in ix.items():
        print(f"  {tid}  {info['category']} (conf {info['confidence']})  "
              f"{info['subject']!r}  from {info['requester']}")


def _resume(thread_id: str, decision: str) -> dict:
    graph = build_graph(get_checkpointer())
    return graph.invoke(Command(resume=decision), {"configurable": {"thread_id": thread_id}})


def cmd_approve(args):
    result = _resume(args.thread_id, "approve")
    print(result.get("outcome"))
    if result.get("draft"):
        print("--- draft ---\n" + result["draft"])
    queue_index.remove(args.thread_id)


def cmd_reject(args):
    result = _resume(args.thread_id, "reject")
    print(result.get("outcome"))
    queue_index.remove(args.thread_id)


def main():
    ap = argparse.ArgumentParser(description="Durable HITL inbox")
    sub = ap.add_subparsers(dest="cmd", required=True)
    run_p = sub.add_parser("run"); run_p.add_argument("--dataset", default=None); run_p.set_defaults(func=cmd_run)
    sub.add_parser("queue").set_defaults(func=cmd_queue)
    a = sub.add_parser("approve"); a.add_argument("thread_id"); a.set_defaults(func=cmd_approve)
    r = sub.add_parser("reject");  r.add_argument("thread_id"); r.set_defaults(func=cmd_reject)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
