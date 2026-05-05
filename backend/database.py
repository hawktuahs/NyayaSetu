"""
NyayaSetu — Database Models & Session
SQLAlchemy async with SQLite. Schema v2 — richer extraction fields.
"""
import json
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean,
    Enum as SAEnum, ForeignKey
)
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, relationship
from config import settings
import enum

Base = declarative_base()
engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


# ── Enums ──────────────────────────────────────────────────────────────────────

class CaseStatus(str, enum.Enum):
    PENDING_EXTRACTION = "pending_extraction"
    EXTRACTING = "extracting"
    PENDING_VERIFICATION = "pending_verification"
    APPROVED = "approved"
    REJECTED = "rejected"


class VerificationDecision(str, enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


class ActionType(str, enum.Enum):
    PROCEED_WITH_IMPLEMENTATION = "proceed_with_implementation"
    COMPLY_WITH_ORDER = "comply_with_order"
    FILE_APPEAL = "file_appeal"
    SEEK_LEGAL_OPINION = "seek_legal_opinion"
    MONITOR_PENDING_PROCEEDINGS = "monitor_pending_proceedings"


class Priority(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class GovernmentOutcome(str, enum.Enum):
    WON = "WON"
    LOST = "LOST"
    PARTIAL = "PARTIAL"
    NOT_APPLICABLE = "NOT APPLICABLE"


# ── Models ─────────────────────────────────────────────────────────────────────

class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    pdf_path = Column(String, nullable=False)
    upload_time = Column(DateTime, default=datetime.utcnow)
    status = Column(SAEnum(CaseStatus), default=CaseStatus.PENDING_EXTRACTION)
    page_count = Column(Integer, default=0)
    extraction_error = Column(Text, nullable=True)
    is_scanned = Column(Boolean, default=False)

    extraction = relationship("Extraction", back_populates="case", uselist=False)
    action_plan = relationship("ActionPlan", back_populates="case", uselist=False)
    verifications = relationship("Verification", back_populates="case")


class Extraction(Base):
    __tablename__ = "extractions"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), unique=True, nullable=False)

    # Core identity
    case_number = Column(String, nullable=True)
    court = Column(String, nullable=True)
    bench_type = Column(String, nullable=True)
    date_of_order = Column(String, nullable=True)
    case_type = Column(String, nullable=True)
    subject_matter = Column(Text, nullable=True)

    # Parties
    appellants = Column(Text, nullable=True)       # JSON array
    respondents = Column(Text, nullable=True)      # JSON array
    appellant_advocate = Column(String, nullable=True)
    respondent_advocate = Column(String, nullable=True)
    judges = Column(Text, nullable=True)           # JSON array

    # Government context
    government_party = Column(String, nullable=True)      # appellant/respondent/both/neither
    government_departments = Column(Text, nullable=True)  # JSON array
    outcome = Column(String, nullable=True)
    outcome_for_government = Column(String, nullable=True)  # WON/LOST/PARTIAL
    operative_order = Column(Text, nullable=True)

    # Directions & timelines
    key_directions = Column(Text, nullable=True)          # JSON array
    stay_status = Column(String, nullable=True)
    next_proceedings = Column(Text, nullable=True)
    compliance_deadline = Column(String, nullable=True)
    appeal_limitation_period = Column(String, nullable=True)
    last_date_for_appeal = Column(String, nullable=True)
    relevant_laws = Column(Text, nullable=True)           # JSON array

    # Summary
    summary = Column(Text, nullable=True)
    raw_extracted_json = Column(Text, nullable=True)
    confidence_scores = Column(Text, nullable=True)       # JSON object
    source_quotes = Column(Text, nullable=True)           # JSON object
    source_pages = Column(Text, nullable=True)            # JSON object
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="extraction")

    def _json_list(self, field):
        val = getattr(self, field)
        if val:
            try:
                return json.loads(val)
            except Exception:
                return []
        return []

    def _json_dict(self, field):
        val = getattr(self, field)
        if val:
            try:
                return json.loads(val)
            except Exception:
                return {}
        return {}

    def get_judges(self): return self._json_list("judges")
    def get_key_directions(self): return self._json_list("key_directions")
    def get_appellants(self): return self._json_list("appellants")
    def get_respondents(self): return self._json_list("respondents")
    def get_government_departments(self): return self._json_list("government_departments")
    def get_relevant_laws(self): return self._json_list("relevant_laws")
    def get_confidence(self): return self._json_dict("confidence_scores")


class ActionPlan(Base):
    __tablename__ = "action_plans"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), unique=True, nullable=False)

    action_type = Column(SAEnum(ActionType), nullable=True)
    priority = Column(SAEnum(Priority), nullable=True)
    urgency_reason = Column(Text, nullable=True)
    critical_flags = Column(Text, nullable=True)        # JSON array
    immediate_actions = Column(Text, nullable=True)     # JSON array
    short_term_actions = Column(Text, nullable=True)    # JSON array
    compliance_timeline = Column(Text, nullable=True)   # JSON array
    appeal_assessment = Column(Text, nullable=True)     # JSON object
    compliance_checklist = Column(Text, nullable=True)  # JSON array
    responsible_authority = Column(String, nullable=True)
    departments_involved = Column(Text, nullable=True)  # JSON array
    risk_if_delayed = Column(Text, nullable=True)
    ai_reasoning = Column(Text, nullable=True)
    technical_reference = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="action_plan")

    def _json(self, field, default):
        val = getattr(self, field)
        if val:
            try:
                return json.loads(val)
            except Exception:
                return default
        return default

    def get_critical_flags(self): return self._json("critical_flags", [])
    def get_immediate_actions(self): return self._json("immediate_actions", [])
    def get_short_term_actions(self): return self._json("short_term_actions", [])
    def get_appeal_assessment(self): return self._json("appeal_assessment", {})
    def get_compliance_checklist(self): return self._json("compliance_checklist", [])
    def get_departments_involved(self): return self._json("departments_involved", [])


class Verification(Base):
    __tablename__ = "verifications"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    reviewer_name = Column(String, nullable=False)
    reviewer_designation = Column(String, nullable=True)
    decision = Column(SAEnum(VerificationDecision), nullable=False)
    edited_extraction_json = Column(Text, nullable=True)
    edited_action_plan_json = Column(Text, nullable=True)
    comment = Column(Text, nullable=True)
    verified_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="verifications")


# ── DB helpers ─────────────────────────────────────────────────────────────────

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
