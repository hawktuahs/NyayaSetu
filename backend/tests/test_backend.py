"""
NyayaSetu — Backend Test Suite
Tests for PDF service, LLM service JSON parsing, and API endpoints.
"""
import json
import pytest
import pytest_asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


# ── PDF Service Tests ──────────────────────────────────────────────────────────

class TestPDFService:
    def test_clean_text_removes_control_chars(self):
        from services.pdf_service import _clean_text
        dirty = "Hello\x00World\x07!\nGood\n\n\n\nBye"
        clean = _clean_text(dirty)
        assert "\x00" not in clean
        assert "\x07" not in clean
        assert clean.count("\n\n\n") == 0  # max 2 consecutive newlines

    def test_extract_pdf_nonexistent_returns_error(self):
        from services.pdf_service import extract_pdf
        result = extract_pdf("/nonexistent/path/file.pdf")
        assert result.error != ""
        assert result.page_count == 0

    def test_get_relevant_pages_finds_keyword(self):
        from services.pdf_service import get_relevant_pages
        full_text = "[PAGE 1]\nThe petitioner filed a writ petition.\n\n[PAGE 2]\nThe court ordered compliance within 30 days."
        results = get_relevant_pages(full_text, "compliance")
        assert len(results) == 1
        assert results[0]["page"] == 2
        assert "compliance" in results[0]["snippet"].lower()

    def test_get_relevant_pages_no_match(self):
        from services.pdf_service import get_relevant_pages
        full_text = "[PAGE 1]\nThis text has no matching terms."
        results = get_relevant_pages(full_text, "xyz_not_found")
        assert results == []


# ── LLM Service JSON Extraction Tests ─────────────────────────────────────────

class TestLLMJSONExtraction:
    def test_plain_json(self):
        from services.llm_service import _extract_json_from_response
        raw = '{"case_number": "WP/123/2024", "court": "High Court"}'
        result = _extract_json_from_response(raw)
        assert result["case_number"] == "WP/123/2024"

    def test_json_with_markdown_fence(self):
        from services.llm_service import _extract_json_from_response
        raw = '```json\n{"case_number": "WP/456/2024"}\n```'
        result = _extract_json_from_response(raw)
        assert result["case_number"] == "WP/456/2024"

    def test_json_with_preamble(self):
        from services.llm_service import _extract_json_from_response
        raw = 'Here is the extracted information:\n\n{"case_number": "WP/789/2024", "court": "HC"}'
        result = _extract_json_from_response(raw)
        assert result["case_number"] == "WP/789/2024"

    def test_invalid_json_raises(self):
        from services.llm_service import _extract_json_from_response
        with pytest.raises(ValueError):
            _extract_json_from_response("This is not JSON at all.")

    def test_validate_extraction_fills_defaults(self):
        from services.llm_service import _validate_extraction
        data = {"case_number": "WP/001/2024"}
        _validate_extraction(data)
        assert "judges" in data
        assert isinstance(data["judges"], list)
        assert "confidence_scores" in data

    def test_validate_action_plan_fills_defaults(self):
        from services.llm_service import _validate_action_plan
        data = {}
        _validate_action_plan(data)
        assert data["action_type"] == "seek_legal_opinion"
        assert data["priority"] == "high"
        assert isinstance(data["critical_flags"], list)
        assert isinstance(data["immediate_actions"], list)
        assert isinstance(data["compliance_checklist"], list)


# ── API Integration Tests ─────────────────────────────────────────────────────

@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def client():
    """Create a test FastAPI client. DB isolation handled by conftest.py."""
    from main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.anyio
async def test_health_endpoint(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "llm_provider" in data
    assert "llm_available" in data


@pytest.mark.anyio
async def test_list_cases_empty(client):
    response = await client.get("/api/cases")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.anyio
async def test_dashboard_stats(client):
    response = await client.get("/api/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_cases" in data
    assert data["total_cases"] == 0


@pytest.mark.anyio
async def test_upload_non_pdf_rejected(client):
    response = await client.post(
        "/api/cases/upload",
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


@pytest.mark.anyio
async def test_get_nonexistent_case(client):
    response = await client.get("/api/cases/99999")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_verification_requires_pending_status(client):
    """Cannot verify a case that hasn't been extracted."""
    # First we need a case - mock the extraction
    with patch("routers.cases._run_extraction", new_callable=AsyncMock):
        # Create a minimal PDF (1 byte won't parse but we just need the record)
        import io
        minimal_pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF"
        response = await client.post(
            "/api/cases/upload",
            files={"file": ("test.pdf", io.BytesIO(minimal_pdf), "application/pdf")},
        )
    # Case will be in pending_extraction state (extraction is mocked)
    # Verification should fail
    if response.status_code == 200:
        case_id = response.json()["id"]
        verify_response = await client.post(
            f"/api/verify/{case_id}",
            json={
                "reviewer_name": "Test Reviewer",
                "decision": "approved",
                "comment": "Test",
            },
        )
        # Should be 400 because case is not in pending_verification state
        assert verify_response.status_code == 400
