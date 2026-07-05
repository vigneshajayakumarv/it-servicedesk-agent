# IT Service Desk Agent

An AI agent that triages an internal IT helpdesk inbox end to end. An email comes in, the agent
reads it, classifies it, pulls what it needs from backing systems, and then either resolves it or —
when it's unsure or the stakes are high — routes it to a human for approval. Every decision is logged
with its reasoning and a confidence score, and a dashboard shows the whole thing running.

Built as a demonstration of the **RPA → AI-automation** shift: not a rule-based bot, but an agent that
*reasons* and *acts* inside a business process, with the production-grade guardrails (human-in-the-loop,
audit trail, observability) that real enterprise automation needs.

## How it works

```
email in
   │
   ▼
classify + extract        ← LLM reasons about intent, pulls structured fields, scores its confidence
   │
   ▼
decide + use tools        ← look up the user, check policy (RAG), draft a reply, create/route a ticket
   │
   ▼
confidence gate (HITL)    ← high-stakes or low-confidence  →  human approval queue
   │                         clear + low-risk               →  auto-resolve
   ▼
audit log + dashboard     ← every decision recorded with reasoning, confidence, and tools used
```

**Domain:** internal IT helpdesk for a fictional company (Northwind Logistics).
**Categories:** password reset · access request · hardware · VPN/network · email · security concern ·
how-to · onboarding/offboarding · other.
**Always escalates:** anything security-related, any access grant, onboarding/offboarding, or anything
the agent isn't confident about.

## Run (Day 1)

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env        # then put your Anthropic API key in .env

python scripts/hello_llm.py
```

You should see each sample email classified into a category with a confidence score and a
`needs_human` flag. That's Day 1 done.

## Layout

```
servicedesk/
  config.py     settings (model, confidence threshold, company)
  schema.py     typed models passed through the pipeline
  llm.py        LLM client — classify() implemented; reasoning/tools layer on later
  ingest.py     load emails (JSON now; Microsoft Graph later)
  hitl.py       confidence gate + human-in-the-loop routing
  audit.py      append-only decision log
  agent/        LangGraph nodes + graph assembly   (built Days 3, 8)
  tools/        directory lookup, policy RAG, actions   (built Days 5–7)
dashboard/      Streamlit app   (built Days 11–13)
data/           sample emails + policy docs
scripts/        hello_llm.py — the Day 1 smoke test
```

## Roadmap

Foundations (1–2) → core reasoning (3–4) → tools (5–7) → orchestration + HITL (8–10) →
dashboard (11–13) → harden + package (14–16). Files for later stages are stubbed with `TODO Day N`
markers so the architecture is visible from the start.
