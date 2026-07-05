"""Typed data models. These are the contract the whole pipeline passes around."""
from __future__ import annotations
from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TicketCategory(str, Enum):
    PASSWORD_RESET = "password_reset"
    ACCESS_REQUEST = "access_request"
    HARDWARE = "hardware"
    VPN_NETWORK = "vpn_network"
    EMAIL_ISSUE = "email_issue"
    SECURITY_CONCERN = "security_concern"
    HOWTO_QUESTION = "howto_question"
    ONBOARDING_OFFBOARDING = "onboarding_offboarding"
    OTHER = "other"


class IncomingEmail(BaseModel):
    id: str
    sender: str
    subject: str
    body: str
    received_at: Optional[datetime] = None


class Classification(BaseModel):
    category: TicketCategory
    confidence: float = Field(ge=0, le=1)
    extracted_fields: dict = Field(default_factory=dict)
    reasoning: str
    suggested_action: str


class AgentDecision(BaseModel):
    email_id: str
    classification: Classification
    requires_human: bool
    tools_called: list[str] = Field(default_factory=list)
    action_taken: Optional[str] = None
    status: str = "pending"   # pending | auto_resolved | awaiting_approval | approved | rejected
