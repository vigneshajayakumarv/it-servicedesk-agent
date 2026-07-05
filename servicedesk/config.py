"""Central config. Reads from .env (see .env.example)."""
import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Default model for the agent's reasoning.
# For cheap/fast high-volume classification, switch to: claude-haiku-4-5-20251001
MODEL = os.getenv("MODEL", "claude-sonnet-4-6")

# Below this classification confidence, the item goes to a human instead of auto-resolving.
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))

# The fictional company the agent supports. Rename to whatever you like.
COMPANY = os.getenv("COMPANY", "Northwind Logistics")
