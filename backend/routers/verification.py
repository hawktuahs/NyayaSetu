"""NyayaSetu — Verification Router v2"""
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import Case, Extraction, Verification, ActionPlan, CaseStatus, VerificationDecision, get_db
from schemas import VerificationCreate, VerificationOut

router = APIRouter(prefix="/api/verify", tags=["verification"])


@router.get("/{case_id}/history", response_model=list[VerificationOut])
async def get_history(case_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Verification).where(Verification.case_id == case_id)
        .order_by(Verification.verified_at.desc())
    )
    return result.scalars().all()


@router.post("/{case_id}", response_model=VerificationOut)
async def submit_verification(
    case_id: int,
    payload: VerificationCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Case)
        .options(selectinload(Case.extraction), selectinload(Case.action_plan))
        .where(Case.id == case_id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "Case not found")

    if case.status not in (CaseStatus.PENDING_VERIFICATION, CaseStatus.APPROVED, CaseStatus.REJECTED):
        raise HTTPException(400, f"Case is in '{case.status}' status — cannot verify yet")

    # Apply edited extraction if provided
    if payload.edited_extraction and case.extraction:
        e = case.extraction
        editable_fields = [
            "case_number", "court", "bench_type", "date_of_order", "case_type",
            "subject_matter", "outcome", "outcome_for_government", "operative_order",
            "compliance_deadline", "appeal_limitation_period", "last_date_for_appeal",
            "stay_status", "next_proceedings", "summary",
        ]
        ed = payload.edited_extraction
        for field in editable_fields:
            if field in ed:
                setattr(e, field, ed[field])

    # Apply edited action plan if provided
    if payload.edited_action_plan and case.action_plan:
        p = case.action_plan
        ap = payload.edited_action_plan
        if "action_type" in ap: p.action_type = ap["action_type"]
        if "priority" in ap: p.priority = ap["priority"]
        if "urgency_reason" in ap: p.urgency_reason = ap["urgency_reason"]
        if "responsible_authority" in ap: p.responsible_authority = ap["responsible_authority"]
        if "risk_if_delayed" in ap: p.risk_if_delayed = ap["risk_if_delayed"]

    # Create verification record
    verification = Verification(
        case_id=case_id,
        reviewer_name=payload.reviewer_name,
        reviewer_designation=payload.reviewer_designation,
        decision=payload.decision,
        comment=payload.comment,
        edited_extraction_json=json.dumps(payload.edited_extraction) if payload.edited_extraction else None,
        edited_action_plan_json=json.dumps(payload.edited_action_plan) if payload.edited_action_plan else None,
    )
    db.add(verification)

    if payload.decision == VerificationDecision.APPROVED:
        case.status = CaseStatus.APPROVED
    else:
        case.status = CaseStatus.REJECTED

    await db.commit()
    await db.refresh(verification)
    return verification
