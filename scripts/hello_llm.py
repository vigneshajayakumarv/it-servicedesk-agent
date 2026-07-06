"""Smoke test: loads the sample emails, runs each through the classifier, prints the result.
Expected: a parsed Classification (category + confidence) printed for each email.

Run from the repo root:  python scripts/hello_llm.py
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from servicedesk.ingest import load_emails
from servicedesk.llm import LLMClient
from servicedesk.hitl import needs_human


def main():
    emails = load_emails()
    client = LLMClient()
    for email in emails:
        result = client.classify(email)
        print("=" * 64)
        print(f"From:    {email.sender}")
        print(f"Subject: {email.subject}")
        print("-" * 64)
        print(json.dumps(result.model_dump(mode="json"), indent=2))
        print(f">> needs_human: {needs_human(result)}")
    print("=" * 64)


if __name__ == "__main__":
    main()
