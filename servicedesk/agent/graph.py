"""Assemble the triage graph with durable human-in-the-loop.

classify -> enrich -> gate -> resolve | human_review
human_review --approve--> resolve ; --reject--> rejected
"""
from __future__ import annotations
from langgraph.graph import StateGraph, START, END

from .nodes import (
    GraphState, classify_node, enrich_node, resolve_node,
    human_review_node, rejected_node, gate, after_review,
)


def build_graph(checkpointer=None):
    b = StateGraph(GraphState)
    b.add_node("classify", classify_node)
    b.add_node("enrich", enrich_node)
    b.add_node("resolve", resolve_node)
    b.add_node("human_review", human_review_node)
    b.add_node("rejected", rejected_node)

    b.add_edge(START, "classify")
    b.add_edge("classify", "enrich")
    b.add_conditional_edges("enrich", gate,
                            {"resolve": "resolve", "human_review": "human_review"})
    b.add_conditional_edges("human_review", after_review,
                            {"resolve": "resolve", "rejected": "rejected"})
    b.add_edge("resolve", END)
    b.add_edge("rejected", END)
    return b.compile(checkpointer=checkpointer)
