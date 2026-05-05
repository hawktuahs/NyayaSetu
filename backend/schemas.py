"""NyayaSetu — Pydantic Schemas v2"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field
from database import CaseStatus, VerificationDecision, ActionType, Priority


class ExtractionOut(BaseModel):
    id: int
    case_id: int
    case_number: Optional[str] = None
    court: Optional[str] = None
    bench_type: Optional[str] = None
    date_of_order: Optional[str] = None
    case_type: Optional[str] = None
    subject_matter: Optional[str] = None
    appellants: list[str] = Field(default_factory=list)
    respondents: list[str] = Field(default_factory=list)
    appellant_advocate: Optional[str] = None
    respondent_advocate: Optional[str] = None
    judges: list[str] = Field(default_factory=list)
    government_party: Optional[str] = None
    government_departments: list[str] = Field(default_factory=list)
    outcome: Optional[str] = None
    outcome_for_government: Optional[str] = None
    operative_order: Optional[str] = None
    key_directions: list[str] = Field(default_factory=list)
    stay_status: Optional[str] = None
    next_proceedings: Optional[str] = None
    compliance_deadline: Optional[str] = None
    appeal_limitation_period: Optional[str] = None
    last_date_for_appeal: Optional[str] = None
    relevant_laws: list[str] = Field(default_factory=list)
    summary: Optional[str] = None
    confidence_scores: dict[str, float] = Field(default_factory=dict)
    source_quotes: dict[str, Optional[str]] = Field(default_factory=dict)
    source_pages: dict[str, Optional[list[int]]] = Field(default_factory=dict)
    created_at: datetime
    model_config = {"from_attributes": True}


class CriticalFlag(BaseModel):
    flag: str
    detail: str
    deadline: Optional[str] = None
    action_required: str


class ActionStep(BaseModel):
    step: int
    action: str
    responsible_officer: str
    deadline: Optional[str] = None
    is_critical: bool = False


class AppealAssessment(BaseModel):
    should_appeal: Any = None
    appeal_forum: Optional[str] = None
    limitation_period: Optional[str] = None
    last_date: Optional[str] = None
    grounds_for_appeal: Optional[str] = None
    recommendation: Optional[str] = None


class ComplianceItem(BaseModel):
    item: str
    status: str = "pending"
    responsible_department: str
    target_date: Optional[str] = None


class TimelineEvent(BaseModel):
    event: str
    date_or_duration: Optional[str] = None
    responsible_party: Optional[str] = None
    status: str = "pending"


class ActionPlanOut(BaseModel):
    id: int
    case_id: int
    action_type: Optional[ActionType]
    priority: Optional[Priority]
    urgency_reason: Optional[str]
    critical_flags: list[CriticalFlag]
    immediate_actions: list[ActionStep]
    short_term_actions: list[ActionStep]
    compliance_timeline: list[TimelineEvent] = Field(default_factory=list)
    appeal_assessment: Optional[AppealAssessment]
    compliance_checklist: list[ComplianceItem]
    responsible_authority: Optional[str]
    departments_involved: list[str]
    risk_if_delayed: Optional[str]
    ai_reasoning: Optional[str]
    technical_reference: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}


class CaseListItem(BaseModel):
    id: int
    filename: str
    original_filename: str
    upload_time: datetime
    status: CaseStatus
    page_count: int
    model_config = {"from_attributes": True}


class CaseDetail(BaseModel):
    id: int
    filename: str
    original_filename: str
    upload_time: datetime
    status: CaseStatus
    page_count: int
    extraction_error: Optional[str]
    extraction: Optional[ExtractionOut] = None
    action_plan: Optional[ActionPlanOut] = None
    model_config = {"from_attributes": True}


class VerificationCreate(BaseModel):
    reviewer_name: str = Field(..., min_length=2)
    reviewer_designation: Optional[str] = None
    decision: VerificationDecision
    comment: Optional[str] = None
    edited_extraction: Optional[dict[str, Any]] = None
    edited_action_plan: Optional[dict[str, Any]] = None


class VerificationOut(BaseModel):
    id: int
    case_id: int
    reviewer_name: str
    reviewer_designation: Optional[str]
    decision: VerificationDecision
    comment: Optional[str]
    verified_at: datetime
    model_config = {"from_attributes": True}


class DashboardCase(BaseModel):
    id: int
    original_filename: str
    upload_time: datetime
    verified_at: Optional[datetime]
    reviewer_name: Optional[str]
    reviewer_designation: Optional[str]
    case_number: Optional[str]
    court: Optional[str]
    date_of_order: Optional[str]
    subject_matter: Optional[str]
    outcome: Optional[str]
    outcome_for_government: Optional[str]
    action_type: Optional[str]
    priority: Optional[str]
    urgency_reason: Optional[str]
    compliance_deadline: Optional[str]
    last_date_for_appeal: Optional[str]
    responsible_authority: Optional[str]
    departments_involved: list[str]
    critical_flags_count: int
    summary: Optional[str]
    status: str
    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    total_cases: int
    pending_verification: int
    approved: int
    rejected: int
    critical_actions: int
    government_won: int
    government_lost: int


class HealthResponse(BaseModel):
    status: str
    llm_provider: str
    llm_model: str
    llm_available: bool
    database: str

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]
