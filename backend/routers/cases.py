"""NyayaSetu — Cases Router v2"""
import json, os, shutil, uuid, logging
from pathlib import Path
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import Case, Extraction, ActionPlan, CaseStatus, get_db
from schemas import CaseListItem, CaseDetail, ChatRequest
from services.pdf_service import extract_pdf, get_relevant_pages
from services.llm_service import extract_judgment_data, generate_action_plan
from config import settings

router = APIRouter(prefix="/api/cases", tags=["cases"])
logger = logging.getLogger(__name__)


def ensure_upload_dir():
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)


@router.post("/upload", response_model=CaseListItem)
async def upload_case(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted.")

    ensure_upload_dir()
    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    pdf_path = Path(settings.upload_dir) / unique_name

    try:
        with open(pdf_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(500, f"File save failed: {e}")

    pdf_result = extract_pdf(pdf_path)

    case = Case(
        filename=unique_name,
        original_filename=file.filename,
        pdf_path=str(pdf_path),
        status=CaseStatus.PENDING_EXTRACTION,
        page_count=pdf_result.page_count,
        is_scanned=pdf_result.is_scanned,
    )
    db.add(case)
    await db.commit()
    await db.refresh(case)

    if pdf_result.error:
        case.extraction_error = f"PDF read error: {pdf_result.error}"
        await db.commit()
    elif pdf_result.is_scanned:
        case.extraction_error = (
            "⚠️ This PDF appears to be scanned/image-based. "
            "Extraction may be poor without OCR."
        )
        await db.commit()

    background_tasks.add_task(_run_extraction, case.id, pdf_result.full_text)
    return case


async def _run_extraction(case_id: int, full_text: str):
    from database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Case).where(Case.id == case_id))
        case = result.scalar_one_or_none()
        if not case:
            return

        case.status = CaseStatus.EXTRACTING
        await db.commit()

        try:
            # Step 1: Extract
            ext_data = await extract_judgment_data(full_text)

            # Auto-fill source_pages if the LLM dropped them
            if "source_pages" not in ext_data or not ext_data["source_pages"]:
                ext_data["source_pages"] = {}
            if "source_quotes" not in ext_data or not ext_data["source_quotes"]:
                ext_data["source_quotes"] = {}

            for key in ["outcome", "operative_order", "stay_status", "case_number", "court", "date_of_order", "compliance_deadline"]:
                val = ext_data.get(key)
                if val and not ext_data["source_pages"].get(key):
                    search_str = str(val)
                    if len(search_str) > 100: search_str = search_str[:100]
                    pages_info = get_relevant_pages(full_text, search_str)
                    if pages_info:
                        ext_data["source_pages"][key] = [pages_info[0]["page"]]
                        if not ext_data["source_quotes"].get(key):
                            ext_data["source_quotes"][key] = str(val)

            def jdump(v):
                return json.dumps(v) if v is not None else None

            extraction = Extraction(
                case_id=case_id,
                case_number=ext_data.get("case_number"),
                court=ext_data.get("court"),
                bench_type=ext_data.get("bench_type"),
                date_of_order=ext_data.get("date_of_order"),
                case_type=ext_data.get("case_type"),
                subject_matter=ext_data.get("subject_matter"),
                appellants=jdump(ext_data.get("appellants", [])),
                respondents=jdump(ext_data.get("respondents", [])),
                appellant_advocate=ext_data.get("appellant_advocate"),
                respondent_advocate=ext_data.get("respondent_advocate"),
                judges=jdump(ext_data.get("judges", [])),
                government_party=ext_data.get("government_party"),
                government_departments=jdump(ext_data.get("government_departments", [])),
                outcome=ext_data.get("outcome"),
                outcome_for_government=ext_data.get("outcome_for_government"),
                operative_order=ext_data.get("operative_order"),
                key_directions=jdump(ext_data.get("key_directions", [])),
                stay_status=ext_data.get("stay_status"),
                next_proceedings=ext_data.get("next_proceedings"),
                compliance_deadline=ext_data.get("compliance_deadline"),
                appeal_limitation_period=ext_data.get("appeal_limitation_period"),
                last_date_for_appeal=ext_data.get("last_date_for_appeal"),
                relevant_laws=jdump(ext_data.get("relevant_laws", [])),
                summary=ext_data.get("summary"),
                raw_extracted_json=json.dumps(ext_data),
                confidence_scores=jdump(ext_data.get("confidence_scores", {})),
                source_quotes=jdump(ext_data.get("source_quotes", {})),
                source_pages=jdump(ext_data.get("source_pages", {})),
            )
            db.add(extraction)
            await db.flush()

            # Step 2: Action Plan
            plan_data = await generate_action_plan(ext_data)

            # Auto-generate timeline if missing
            if not plan_data.get("compliance_timeline"):
                plan_data["compliance_timeline"] = []
                if plan_data.get("immediate_actions"):
                    for idx, a in enumerate(plan_data["immediate_actions"]):
                        plan_data["compliance_timeline"].append({
                            "event": a.get("action", f"Immediate Action {idx+1}"),
                            "date_or_duration": a.get("deadline", "Within 48 hours"),
                            "responsible_party": a.get("responsible_officer", plan_data.get("responsible_authority", "Concerned Authority")),
                            "status": "pending"
                        })
                if plan_data.get("short_term_actions"):
                    for idx, a in enumerate(plan_data["short_term_actions"]):
                        plan_data["compliance_timeline"].append({
                            "event": a.get("action", f"Short Term Action {idx+1}"),
                            "date_or_duration": a.get("deadline", "Next 2 weeks"),
                            "responsible_party": a.get("responsible_officer", plan_data.get("responsible_authority", "Concerned Authority")),
                            "status": "pending"
                        })

            plan = ActionPlan(
                case_id=case_id,
                action_type=plan_data.get("action_type", "seek_legal_opinion"),
                priority=plan_data.get("priority", "high"),
                urgency_reason=plan_data.get("urgency_reason"),
                critical_flags=jdump(plan_data.get("critical_flags", [])),
                immediate_actions=jdump(plan_data.get("immediate_actions", [])),
                short_term_actions=jdump(plan_data.get("short_term_actions", [])),
                compliance_timeline=jdump(plan_data.get("compliance_timeline", [])),
                appeal_assessment=jdump(plan_data.get("appeal_assessment", {})),
                compliance_checklist=jdump(plan_data.get("compliance_checklist", [])),
                responsible_authority=plan_data.get("responsible_authority"),
                departments_involved=jdump(plan_data.get("departments_involved", [])),
                risk_if_delayed=plan_data.get("risk_if_delayed"),
                ai_reasoning=plan_data.get("ai_reasoning"),
                technical_reference=plan_data.get("technical_reference"),
            )
            db.add(plan)
            case.status = CaseStatus.PENDING_VERIFICATION
            await db.commit()
            logger.info(f"Extraction complete for case {case_id}")

        except Exception as e:
            logger.error(f"Extraction failed for case {case_id}: {e}")
            case.status = CaseStatus.PENDING_EXTRACTION
            case.extraction_error = f"{case.extraction_error or ''}\nExtraction error: {str(e)[:600]}"
            await db.commit()


@router.get("", response_model=list[CaseListItem])
async def list_cases(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Case).order_by(Case.upload_time.desc()))
    return result.scalars().all()


@router.get("/{case_id}", response_model=CaseDetail)
async def get_case(case_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Case)
        .options(selectinload(Case.extraction), selectinload(Case.action_plan))
        .where(Case.id == case_id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "Case not found")

    cd = {
        "id": case.id, "filename": case.filename,
        "original_filename": case.original_filename,
        "upload_time": case.upload_time, "status": case.status,
        "page_count": case.page_count, "extraction_error": case.extraction_error,
        "extraction": None, "action_plan": None,
    }

    if case.extraction:
        e = case.extraction
        cd["extraction"] = {
            "id": e.id, "case_id": e.case_id,
            "case_number": e.case_number, "court": e.court,
            "bench_type": e.bench_type, "date_of_order": e.date_of_order,
            "case_type": e.case_type, "subject_matter": e.subject_matter,
            "appellants": e.get_appellants(), "respondents": e.get_respondents(),
            "appellant_advocate": e.appellant_advocate,
            "respondent_advocate": e.respondent_advocate,
            "judges": e.get_judges(),
            "government_party": e.government_party,
            "government_departments": e.get_government_departments(),
            "outcome": e.outcome,
            "outcome_for_government": e.outcome_for_government,
            "operative_order": e.operative_order,
            "key_directions": e.get_key_directions(),
            "stay_status": e.stay_status,
            "next_proceedings": e.next_proceedings,
            "compliance_deadline": e.compliance_deadline,
            "appeal_limitation_period": e.appeal_limitation_period,
            "last_date_for_appeal": e.last_date_for_appeal,
            "relevant_laws": e.get_relevant_laws(),
            "summary": e.summary,
            "confidence_scores": e.get_confidence(),
            "source_quotes": json.loads(e.source_quotes) if hasattr(e, 'source_quotes') and e.source_quotes else {},
            "source_pages": json.loads(e.source_pages) if hasattr(e, 'source_pages') and e.source_pages else {},
            "created_at": e.created_at,
        }

    if case.action_plan:
        p = case.action_plan
        ap_raw = p.get_appeal_assessment()
        cd["action_plan"] = {
            "id": p.id, "case_id": p.case_id,
            "action_type": p.action_type, "priority": p.priority,
            "urgency_reason": p.urgency_reason,
            "critical_flags": p.get_critical_flags(),
            "immediate_actions": p.get_immediate_actions(),
            "short_term_actions": p.get_short_term_actions(),
            "compliance_timeline": json.loads(p.compliance_timeline) if hasattr(p, 'compliance_timeline') and p.compliance_timeline else [],
            "appeal_assessment": ap_raw if isinstance(ap_raw, dict) else {},
            "compliance_checklist": p.get_compliance_checklist(),
            "responsible_authority": p.responsible_authority,
            "departments_involved": p.get_departments_involved(),
            "risk_if_delayed": p.risk_if_delayed,
            "ai_reasoning": p.ai_reasoning,
            "technical_reference": p.technical_reference,
            "created_at": p.created_at,
        }

    return cd


@router.post("/{case_id}/retry")
async def retry_extraction(case_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "Case not found")

    pdf_result = extract_pdf(case.pdf_path)
    if pdf_result.error:
        raise HTTPException(400, f"PDF error: {pdf_result.error}")

    # Delete old extraction
    from database import Extraction as ExtModel, ActionPlan as PlanModel
    old_ext = await db.execute(select(ExtModel).where(ExtModel.case_id == case_id))
    old_ext = old_ext.scalar_one_or_none()
    if old_ext:
        await db.delete(old_ext)

    old_plan = await db.execute(select(PlanModel).where(PlanModel.case_id == case_id))
    old_plan = old_plan.scalar_one_or_none()
    if old_plan:
        await db.delete(old_plan)

    case.status = CaseStatus.PENDING_EXTRACTION
    case.extraction_error = None
    await db.commit()

    background_tasks.add_task(_run_extraction, case.id, pdf_result.full_text)
    return {"message": "Extraction re-triggered", "case_id": case_id}

@router.post("/{case_id}/chat")
async def chat_with_case_document(case_id: int, request: ChatRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "Case not found")

    pdf_result = extract_pdf(case.pdf_path)
    if pdf_result.error:
        raise HTTPException(400, f"PDF error: {pdf_result.error}")

    from services.llm_service import LLMService
    llm = LLMService()
    try:
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        reply = await llm.chat_with_document(pdf_result.full_text, messages)
        return {"reply": reply}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(500, f"Chat processing failed: {str(e)}")
