import pytest
import json
from services.llm_service import _extract_json_from_response
from database import ActionPlan, ActionType, Priority

def test_action_plan_enum_validation():
    """Verify that ActionPlan handles enums correctly."""
    plan = ActionPlan(
        case_id=1,
        action_type=ActionType.FILE_APPEAL,
        priority=Priority.CRITICAL,
        urgency_reason="Deadline approaching",
        critical_flags=json.dumps([{"flag": "Limitation", "detail": "30 days"}]),
        compliance_timeline=json.dumps([{"event": "Filing", "date_or_duration": "Tomorrow"}])
    )
    
    assert plan.action_type == ActionType.FILE_APPEAL
    assert plan.priority == Priority.CRITICAL
    assert len(plan.get_critical_flags()) == 1
    assert plan.get_critical_flags()[0]["flag"] == "Limitation"

def test_llm_json_parsing_robustness():
    """Verify that the llm_service can handle slightly malformed JSON from LLM."""
    malformed_json = '```json\n{"case_number": "WP 123", "court": "High Court"}\n```'
    parsed = _extract_json_from_response(malformed_json)
    assert parsed["case_number"] == "WP 123"
    
    extra_text_json = 'The extraction is: {"case_number": "WP 456"}'
    parsed2 = _extract_json_from_response(extra_text_json)
    assert parsed2["case_number"] == "WP 456"

def test_pydantic_validation():
    """Verify pydantic model for extraction output."""
    from schemas import ExtractionOut
    from datetime import datetime
    
    ext_data = {
        "id": 1,
        "case_id": 10,
        "case_number": "123",
        "court": "Karnataka High Court",
        "outcome_for_government": "WON",
        "appellants": [],
        "respondents": [],
        "judges": [],
        "government_departments": [],
        "key_directions": [],
        "relevant_laws": [],
        "confidence_scores": {},
        "created_at": datetime.now()
    }
    obj = ExtractionOut(**ext_data)
    assert obj.outcome_for_government == "WON"
    assert obj.court == "Karnataka High Court"
