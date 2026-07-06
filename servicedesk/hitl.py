"""Confidence gate + human-in-the-loop routing. This is the enterprise-grade bit.
Two independent rules: high-stakes categories always go to a human; low confidence does too."""
from . import config
from .schema import Classification, TicketCategory

# Always require a human sign-off, even at high confidence, because these touch
# security or grant/remove access. Auto-resolving these would be the dangerous move.
HIGH_STAKES = {
    TicketCategory.SECURITY_CONCERN,
    TicketCategory.ACCESS_REQUEST,
    TicketCategory.ONBOARDING_OFFBOARDING,
}


def needs_human(c: Classification) -> bool:
    if c.category in HIGH_STAKES:
        return True
    if c.confidence < config.CONFIDENCE_THRESHOLD:
        return True
    return False
