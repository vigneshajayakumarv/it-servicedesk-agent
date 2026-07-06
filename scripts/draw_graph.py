"""Print a Mermaid diagram of the compiled graph. Paste the output into
https://mermaid.live to see the flow.

Run:  python scripts/draw_graph.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from servicedesk.agent.graph import build_graph

print(build_graph().get_graph().draw_mermaid())
