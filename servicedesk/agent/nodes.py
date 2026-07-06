"""LangGraph nodes: durable human-in-the-loop + audit trail.

State carries plain dicts/strings (checkpoint-safe). Each agent decision is written to
the append-only audit log in the node where it runs exactly once. The escalation event
is logged by the runner (the human_review node re-runs on resume, so logging there
would double-write).

Flow: classify -> enrich -> gate -> resolve | human_review
      human_review --approve--> resolve ; --reject--> rejected
"""
from __future__ import annotations
from typing import TypedDict, Optional

from langgraph.types import interrupt

from ..schema import IncomingEmail, Classification
from ..llm import LLMClient
from ..hitl import needs_human
from ..tools.directory import lookup_user
from ..tools.policy import check_policy
from ..tools.actions import draft_reply, create_ticket
from .. import audit


class GraphState(TypedDict, total=False):
    email: dict
    classification: dict
    user: Optional[dict]
    policy: str
    decision: str
    draft: str
    ticket_id: str
    outcome: str


_client: Optional[LLMClient] = None
def _get_client() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client


def classify_node(state: GraphState) -> dict:
    email = IncomingEmail(**state["email"])
    c = _get_client().classify(email)
    print(f"  [classify] {email.id} -> {c.category.value} ({c.confidence:.2f})")
    audit.record(email.id, "classified", "agent",
                 c.category.value, c.confidence, c.reasoning)
    return {"classification": c.model_dump(mode="json")}


def enrich_node(state: GraphState) -> dict:
    email = IncomingEmail(**state["email"])
    c = Classification(**state["classification"])
    user = lookup_user(email.sender)
    policy = check_policy(c.suggested_action or email.subject)
    print(f"  [enrich]   user={'found' if user else 'unknown'}, policy retrieved")
    return {"user": user, "policy": policy}


def human_review_node(state: GraphState) -> dict:
    """PAUSE for human approval. interrupt() is the first call - no side effects (incl.
    audit writes) above it, since the node re-runs from the top on resume."""
    email = state["email"]
    c = Classification(**state["classification"])
    decision = interrupt({
        "email_id": email["id"],
        "requester": email["sender"],
        "subject": email["subject"],
        "category": c.category.value,
        "confidence": c.confidence,
        "action": "Approve to draft a reply + open a ticket, or reject to decline.",
    })
    d = decision if isinstance(decision, str) else str(decision.get("decision", ""))
    return {"decision": d.strip().lower()}


def resolve_node(state: GraphState) -> dict:
    email = IncomingEmail(**state["email"])
    c = Classification(**state["classification"])
    draft = draft_reply(email, c, user=state.get("user"), policy=state.get("policy", ""))
    ticket_id = create_ticket(email, c)
    path = "approved" if state.get("decision") else "auto"
    print(f"  [resolve]  drafted reply + ticket {ticket_id}")
    audit.record(email.id, "resolved", "agent", c.category.value, c.confidence,
                 f"path={path}; ticket={ticket_id}")
    return {"draft": draft, "ticket_id": ticket_id,
            "outcome": f"RESOLVED ({c.category.value}) -> {ticket_id}"}


def rejected_node(state: GraphState) -> dict:
    email = IncomingEmail(**state["email"])
    c = Classification(**state["classification"])
    print(f"  [rejected] {email.id} declined by human")
    audit.record(email.id, "rejected", "human", c.category.value, c.confidence,
                 "declined by human")
    return {"outcome": f"REJECTED by human ({c.category.value})"}


def gate(state: GraphState) -> str:
    return "human_review" if needs_human(Classification(**state["classification"])) else "resolve"


def after_review(state: GraphState) -> str:
    return "resolve" if state.get("decision", "").startswith("a") else "rejected"
