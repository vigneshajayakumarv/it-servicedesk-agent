"""LLM client with graceful failure handling.

If classification fails - API error after retries, or unparseable/invalid output - it
falls back to a zero-confidence 'other', which the gate routes to a HUMAN. A failure
never crashes the batch and never silently auto-acts; it escalates. Same safety
principle as the confidence gate, applied to failures.
"""
from __future__ import annotations
import json
import anthropic

from . import config
from .schema import IncomingEmail, Classification, TicketCategory

SYSTEM = """You are an IT service desk triage agent for {company}.
Read the incoming employee email, classify it into exactly ONE category, and extract useful fields.

Categories:
- password_reset       account locked, forgotten password, MFA reset
- access_request       needs a license / app / shared drive / elevated access
- hardware             laptop, monitor, peripherals, physical device faults
- vpn_network          VPN, wifi, connectivity
- email_issue          Outlook / mailbox / distribution list problems
- security_concern     phishing report, suspected compromise, malware, data exposure
- howto_question       general "how do I..." guidance
- onboarding_offboarding   new hire setup or leaver deprovisioning
- other                anything that fits none of the above

Return ONLY a JSON object, no prose and no code fences, with these keys:
  category          one of the category ids above
  confidence        number 0-1, how sure you are of the category
  extracted_fields  object of any useful fields you can pull (e.g. user_name, employee_id, app_name, device, urgency)
  reasoning         one short sentence on why you chose that category
  suggested_action  one short sentence on what should happen next
"""


class LLMClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        key = api_key or config.ANTHROPIC_API_KEY
        if not key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        self.client = anthropic.Anthropic(api_key=key)
        self.model = model or config.MODEL

    def classify(self, email: IncomingEmail) -> Classification:
        prompt = f"From: {email.sender}\nSubject: {email.subject}\n\n{email.body}"
        last_err: Exception | None = None
        for _ in range(2):  # one retry on transient error / malformed output
            try:
                resp = self.client.messages.create(
                    model=self.model, max_tokens=512,
                    system=SYSTEM.format(company=config.COMPANY),
                    messages=[{"role": "user", "content": prompt}],
                )
                text = "".join(b.text for b in resp.content if b.type == "text").strip()
                return Classification(**json.loads(_strip_fences(text)))
            except Exception as e:
                last_err = e
        # fail safe: zero confidence -> the gate routes this to a human for manual review.
        return Classification(
            category=TicketCategory.OTHER, confidence=0.0,
            reasoning=f"automatic classification failed ({type(last_err).__name__}); routing to a human",
            suggested_action="Manual review required (automatic classification failed).",
        )

    def complete(self, system: str, user: str, max_tokens: int = 600) -> str:
        """General completion for drafting. Returns '' on failure so the caller can fall back."""
        try:
            resp = self.client.messages.create(
                model=self.model, max_tokens=max_tokens,
                system=system, messages=[{"role": "user", "content": user}],
            )
            return "".join(b.text for b in resp.content if b.type == "text").strip()
        except Exception:
            return ""


def _strip_fences(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else ""
        if s.rstrip().endswith("```"):
            s = s.rsplit("```", 1)[0]
    return s.strip()
