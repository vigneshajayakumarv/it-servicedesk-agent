"""IT Service Desk Agent - operations dashboard (Streamlit).

Live operational metrics + audit trail + pending queue + tickets, with approve/reject
that resumes the durable graph by thread_id. A separate 'Model quality' panel shows
classification accuracy measured on the held-out labeled set (never live traffic).

Run from the repo root:  streamlit run dashboard/app.py
"""
import sys, os, json, sqlite3
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from langgraph.types import Command

from servicedesk import audit, queue_index, metrics
from servicedesk.agent.graph import build_graph
from servicedesk.checkpoint import get_checkpointer
from servicedesk.tools.actions import TICKETS_DB

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL_FILE = os.path.join(_ROOT, "data", "eval_results.json")

st.set_page_config(page_title="IT Service Desk Agent", layout="wide")
st.title("IT Service Desk Agent - Operations")

# --- demo bootstrap (cloud filesystems start empty) ---
def _run_demo_inbox():
    """Seed the directory if needed, then process the 5 sample emails through the graph."""
    import sqlite3 as _sq
    from servicedesk.tools.directory import DB as DIR_DB
    if not os.path.exists(DIR_DB):
        sys.path.insert(0, os.path.join(_ROOT, "scripts"))
        import seed_directory
        seed_directory.main()
    from servicedesk.ingest import load_emails
    g = build_graph(get_checkpointer())
    done = paused = 0
    for email in load_emails():
        cfg = {"configurable": {"thread_id": email.id}}
        r = g.invoke({"email": email.model_dump(mode="json")}, cfg)
        if "__interrupt__" in r:
            pv = r["__interrupt__"][0].value
            queue_index.add(email.id, {k: pv.get(k) for k in ("requester", "subject", "category", "confidence")})
            audit.record(email.id, "escalated", "agent", pv.get("category"), pv.get("confidence"), "awaiting human approval")
            paused += 1
        else:
            done += 1
    return done, paused

if not audit.all_email_ids():
    st.info("No data yet - this instance starts empty. Process the demo inbox to see the agent work.")
    if st.button("Run demo inbox (5 sample emails)", type="primary"):
        with st.spinner("Classifying, enriching, and routing 5 emails... (~30s)"):
            done, paused = _run_demo_inbox()
        st.success(f"Processed 5 emails: {done} auto-resolved, {paused} awaiting your approval below.")
        st.rerun()

# Result banner from the most recent approve/reject (survives the rerun).
if "last_result" in st.session_state:
    lr = st.session_state.pop("last_result")
    (st.success if lr["ok"] else st.warning)(lr["outcome"])
    if lr.get("draft"):
        with st.expander("Drafted reply", expanded=True):
            st.text(lr["draft"])

# --- live operational metrics (from the audit table) ---
ops = metrics.operational()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Emails processed", ops["processed"])
c2.metric("Auto-resolution rate", f"{ops['auto_rate']*100:.0f}%")
c3.metric("Est. hours saved", f"{ops['hours_saved']:.1f}")
c4.metric("Pending approval", ops["pending"])
st.caption(f"{ops['auto_resolved']} auto-resolved · {ops['approved']} approved · "
           f"{ops['rejected']} rejected · {ops['escalated']} escalated")

st.divider()

# --- pending approvals (approve/reject resume the durable graph) ---
st.subheader("Pending approvals")
pending = queue_index.load()
if not pending:
    st.info("Nothing awaiting approval. Run the inbox:  python scripts/inbox.py run")
else:
    for tid, info in pending.items():
        with st.container(border=True):
            st.markdown(f"**{tid}** — {info.get('category')} · confidence {info.get('confidence')}")
            st.caption(f"From {info.get('requester')} — {info.get('subject')}")
            col_a, col_r, _ = st.columns([1, 1, 5])
            if col_a.button("Approve", key=f"ap_{tid}", type="primary"):
                with st.spinner("Resuming and drafting reply..."):
                    g = build_graph(get_checkpointer())
                    res = g.invoke(Command(resume="approve"), {"configurable": {"thread_id": tid}})
                    queue_index.remove(tid)
                st.session_state["last_result"] = {"ok": True, "outcome": res.get("outcome"), "draft": res.get("draft")}
                st.rerun()
            if col_r.button("Reject", key=f"rj_{tid}"):
                with st.spinner("Resuming..."):
                    g = build_graph(get_checkpointer())
                    res = g.invoke(Command(resume="reject"), {"configurable": {"thread_id": tid}})
                    queue_index.remove(tid)
                st.session_state["last_result"] = {"ok": False, "outcome": res.get("outcome")}
                st.rerun()

st.divider()

# --- tickets ---
st.subheader("Tickets")
if os.path.exists(TICKETS_DB):
    con = sqlite3.connect(TICKETS_DB)
    rows = con.execute(
        "SELECT ticket_id, requester, category, queue, status, created_at "
        "FROM tickets ORDER BY created_at DESC").fetchall()
    con.close()
    cols = ["ticket", "requester", "category", "queue", "status", "created"]
    st.dataframe([dict(zip(cols, r)) for r in rows], width='stretch', hide_index=True)
else:
    st.info("No tickets yet.")

st.divider()

# --- audit trail ---
st.subheader("Audit trail")
events = []
for eid in audit.all_email_ids():
    for ts, event, actor, cat, conf, detail in audit.events_for(eid):
        events.append({"time": ts[11:19], "email": eid, "event": event,
                       "actor": actor, "category": cat, "confidence": conf, "detail": detail})
events.sort(key=lambda e: e["time"], reverse=True)
if events:
    st.dataframe(events, width='stretch', hide_index=True)
else:
    st.info("No audit events yet.")

st.divider()

# --- model quality (separate: measured on the held-out labeled eval set) ---
st.subheader("Model quality — evaluation set")
if os.path.exists(EVAL_FILE):
    ev = json.load(open(EVAL_FILE))
    m1, m2 = st.columns(2)
    m1.metric("Classification accuracy", f"{ev['accuracy']*100:.0f}%",
              help=f"{ev['correct']}/{ev['total']} correct on the held-out labeled emails")
    m2.metric("Low-confidence (<0.75)", f"{ev['low_confidence']}/{ev['total']}")
    st.caption("Measured on the 30 labeled emails (held-out eval set), not live traffic. "
               "Uncertain items route to a human, so a low-confidence classification is caught, not acted on.")
    st.dataframe(
        [{"difficulty": d, "accuracy": f"{v['correct']}/{v['total']}"}
         for d, v in ev["by_difficulty"].items()],
        width='stretch', hide_index=True)
else:
    st.info("Run:  python scripts/eval_dataset.py  to populate model-quality metrics.")
