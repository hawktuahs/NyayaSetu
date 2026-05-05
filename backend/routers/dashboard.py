"""NyayaSetu — Dashboard Router v2"""
import json
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from database import Case, Extraction, ActionPlan, Verification, CaseStatus, Priority, get_db
from schemas import DashboardCase, DashboardStats

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=list[DashboardCase])
async def get_dashboard_cases(
    department: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    outcome: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Case)
        .options(
            selectinload(Case.extraction),
            selectinload(Case.action_plan),
            selectinload(Case.verifications),
        )
        .where(Case.status == CaseStatus.APPROVED)
        .order_by(Case.upload_time.desc())
    )
    cases = result.scalars().all()

    rows = []
    for case in cases:
        e = case.extraction
        p = case.action_plan
        last_v = (
            sorted(case.verifications, key=lambda v: v.verified_at, reverse=True)[0]
            if case.verifications else None
        )

        dept_list = e.get_government_departments() if e else []
        prio = p.priority.value if (p and p.priority) else None
        out = e.outcome_for_government if e else None
        flags = p.get_critical_flags() if p else []
        depts = p.get_departments_involved() if p else []

        if department and not any(department.lower() in d.lower() for d in (dept_list + depts)):
            continue
        if priority and prio and priority.lower() != prio.lower():
            continue
        if outcome and out and outcome.upper() != out.upper():
            continue

        rows.append(DashboardCase(
            id=case.id,
            original_filename=case.original_filename,
            upload_time=case.upload_time,
            verified_at=last_v.verified_at if last_v else None,
            reviewer_name=last_v.reviewer_name if last_v else None,
            reviewer_designation=last_v.reviewer_designation if last_v else None,
            case_number=e.case_number if e else None,
            court=e.court if e else None,
            date_of_order=e.date_of_order if e else None,
            subject_matter=e.subject_matter if e else None,
            outcome=e.outcome if e else None,
            outcome_for_government=e.outcome_for_government if e else None,
            action_type=p.action_type.value if (p and p.action_type) else None,
            priority=prio,
            urgency_reason=p.urgency_reason if p else None,
            compliance_deadline=e.compliance_deadline if e else None,
            last_date_for_appeal=e.last_date_for_appeal if e else None,
            responsible_authority=p.responsible_authority if p else None,
            departments_involved=depts,
            critical_flags_count=len(flags),
            summary=e.summary if e else None,
            status=case.status.value,
        ))

    # Sort by priority
    prio_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    rows.sort(key=lambda r: prio_order.get(r.priority or "low", 9))
    return rows


@router.get("/stats", response_model=DashboardStats)
async def get_stats(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count(Case.id)))).scalar_one()
    pending = (await db.execute(
        select(func.count(Case.id)).where(Case.status == CaseStatus.PENDING_VERIFICATION)
    )).scalar_one()
    approved = (await db.execute(
        select(func.count(Case.id)).where(Case.status == CaseStatus.APPROVED)
    )).scalar_one()
    rejected = (await db.execute(
        select(func.count(Case.id)).where(Case.status == CaseStatus.REJECTED)
    )).scalar_one()

    critical = (await db.execute(
        select(func.count(ActionPlan.id))
        .join(Case, ActionPlan.case_id == Case.id)
        .where(Case.status == CaseStatus.APPROVED)
        .where(ActionPlan.priority == Priority.CRITICAL)
    )).scalar_one()

    # Government won/lost counts from approved cases
    won_q = (await db.execute(
        select(func.count(Case.id))
        .join(Extraction, Extraction.case_id == Case.id)
        .where(Case.status == CaseStatus.APPROVED)
        .where(Extraction.outcome_for_government == "WON")
    )).scalar_one()

    lost_q = (await db.execute(
        select(func.count(Case.id))
        .join(Extraction, Extraction.case_id == Case.id)
        .where(Case.status == CaseStatus.APPROVED)
        .where(Extraction.outcome_for_government == "LOST")
    )).scalar_one()

    return DashboardStats(
        total_cases=total,
        pending_verification=pending,
        approved=approved,
        rejected=rejected,
        critical_actions=critical,
        government_won=won_q,
        government_lost=lost_q,
    )
