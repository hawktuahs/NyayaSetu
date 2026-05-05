"""
NyayaSetu — LLM Service
Multi-provider LLM abstraction with legally-tuned extraction prompts.
Engineered specifically for Indian High Court / Supreme Court judgment analysis.
"""
import json
import re
import logging
import httpx
from config import settings

logger = logging.getLogger(__name__)

# ── System Prompts ─────────────────────────────────────────────────────────────

EXTRACTION_SYSTEM = """You are a senior legal analyst specializing in Indian court judgments for the Government's Court Case Monitoring System (CCMS).

Your task is to extract EXACTLY the information requested from court judgments and return ONLY valid JSON.

Key rules:
- Extract ONLY what is explicitly stated in the document. Do not infer or fabricate.
- For government departments as appellants/respondents: identify the SPECIFIC department name.
- "Outcome for Government" field is critical: clearly state whether the government WON or LOST.
- For the operative order (final decision), look for phrases like "appeal is allowed", "petition is dismissed", "order is set aside", "writ petition is allowed/dismissed".
- Confidence scores (0.0-1.0) reflect how clearly the field appears in the document.
- If a field is not present, use null — never guess.
- CRITICAL: You MUST include 'source_quotes' and 'source_pages' dicts for verification.
- Return ONLY the JSON object. No markdown, no explanation, no preamble."""

EXTRACTION_USER = """Extract structured legal information from this Indian court judgment.

JUDGMENT TEXT:
{text}

Return ONLY this JSON (no markdown, no extra text):
{{
  "case_number": "e.g. WA No. 541 of 2026 or WP/123/2024",
  "court": "Full court name e.g. High Court of Karnataka at Bengaluru",
  "bench_type": "Single Judge / Division Bench / Full Bench",
  "date_of_order": "DD/MM/YYYY",
  "case_type": "Writ Appeal / Writ Petition / Civil Appeal / Criminal Appeal / etc.",
  "subject_matter": "One sentence: what is this case about (e.g. liquor licensing rules challenge)",
  "appellants": ["Name / Description of appellant 1", "Name 2"],
  "respondents": ["Name / Description of respondent 1", "Name 2"],
  "appellant_advocate": "Lead advocate for appellant",
  "respondent_advocate": "Lead advocate for respondent",
  "judges": ["Full name and designation e.g. Vibhu Bakhru, Chief Justice"],
  "government_party": "appellant" | "respondent" | "both" | "neither",
  "government_departments": ["Department 1", "Department 2"],
  "outcome": "Appeal Allowed / Appeal Dismissed / Petition Allowed / Petition Dismissed / Order Set Aside / etc.",
  "outcome_for_government": "WON" | "LOST" | "PARTIAL" | "NOT APPLICABLE",
  "operative_order": "Exact verbatim text of the final order/direction (last paragraphs)",
  "key_directions": [
    "Specific direction 1 — exactly what the court has ordered",
    "Specific direction 2"
  ],
  "stay_status": "Stay granted / Stay vacated / Stay continued / No stay / Not applicable",
  "next_proceedings": "What happens next in this case (e.g. matter goes back to Single Judge, main petition still pending, etc.)",
  "compliance_deadline": "Specific date or duration if ordered, otherwise null",
  "appeal_limitation_period": "e.g. 30 days from date of order for Letters Patent Appeal / 90 days for SLP to Supreme Court",
  "last_date_for_appeal": "Computed date if possible, otherwise null",
  "relevant_laws": ["Act/Rule 1", "Act/Rule 2"],
  "summary": "3-4 sentence plain English summary of what happened and what the government must do now",
  "confidence_scores": {{
    "outcome": 0.9,
    "operative_order": 0.8,
    "compliance_deadline": 0.5
  }},
  "source_quotes": {{
    "outcome": "Exact 1-2 sentence quote proving the outcome",
    "operative_order": "Exact quote of the final order/direction",
    "compliance_deadline": "Exact quote containing the deadline"
  }},
  "source_pages": {{
    "outcome": [45],
    "operative_order": [46, 47],
    "compliance_deadline": [46]
  }}
}}
IMPORTANT: Identify the source pages by looking for the [PAGE X] markers in the text. Return the integer page numbers in the source_pages dict."""

# ── Action Plan Prompt ─────────────────────────────────────────────────────────

ACTION_PLAN_SYSTEM = """You are a senior legal advisor to the Government of India with 30 years of experience in administrative law.

Based on extracted court judgment data, generate a precise, actionable administrative action plan for the government department.

Rules:
- If the government WON (outcome_for_government = WON): primary action is to PROCEED with implementation. Secondary: monitor for further appeals.
- If the government LOST (outcome_for_government = LOST): primary decision is COMPLY vs APPEAL. Evaluate on merits.
- Always compute concrete deadlines. If a stay was vacated, urgent action is required.
- CRITICAL: You MUST generate a step-by-step 'compliance_timeline' array.
- The action plan must be IMMEDIATELY actionable by a mid-level bureaucrat who has NOT read the full judgment.
- Return ONLY valid JSON. No preamble."""

ACTION_PLAN_USER = """Based on this court judgment extraction, create a complete administrative action plan:

EXTRACTED JUDGMENT DATA:
{extraction_json}

Return ONLY this JSON:
{{
  "action_type": "proceed_with_implementation" | "comply_with_order" | "file_appeal" | "seek_legal_opinion" | "monitor_pending_proceedings",
  "priority": "critical" | "high" | "medium" | "low",
  "urgency_reason": "One sentence explaining WHY this priority level (e.g. 'Stay vacated — auction can now proceed immediately')",
  "critical_flags": [
    {{
      "flag": "Short description of critical item",
      "detail": "Explanation",
      "deadline": "Date or duration or null",
      "action_required": "What exactly must be done"
    }}
  ],
  "immediate_actions": [
    {{
      "step": 1,
      "action": "Specific action to take within 48 hours",
      "responsible_officer": "Designation e.g. Commissioner of Excise",
      "deadline": "Within 48 hours / by DD/MM/YYYY",
      "is_critical": true
    }}
  ],
  "short_term_actions": [
    {{
      "step": 1,
      "action": "Action within 1-4 weeks",
      "responsible_officer": "Designation",
      "deadline": "Timeframe",
      "is_critical": false
    }}
  ],
  "appeal_assessment": {{
    "should_appeal": true | false | "already_favourable",
    "appeal_forum": "Division Bench / Supreme Court (SLP) / Not applicable",
    "limitation_period": "30 days / 90 days / null",
    "last_date": "DD/MM/YYYY or null",
    "grounds_for_appeal": "If applicable, summarize grounds. If government won, state 'Not required - judgment in government's favour'",
    "recommendation": "File appeal / Do not appeal / Government won — no appeal required"
  }},
  "compliance_checklist": [
    {{
      "item": "Specific compliance item",
      "status": "pending",
      "responsible_department": "Department name",
      "target_date": "Date or timeframe"
    }}
  ],
  "compliance_timeline": [
    {{
      "event": "Step-by-step chronological event or milestone",
      "date_or_duration": "Exact date or time frame (e.g. 'Within 4 weeks')",
      "responsible_party": "Who must do this",
      "status": "pending"
    }}
  ],
  "responsible_authority": "Primary authority responsible for all actions",
  "departments_involved": ["Department 1", "Department 2"],
  "risk_if_delayed": "Plain English: what happens if the government doesn't act promptly",
  "ai_reasoning": "Detailed 3-4 sentences explaining the basis for this action plan. Include a feasibility assessment of the immediate actions and justify the priority.",
  "technical_reference": "Specific legal or technical references (acts, sections, circulars, or precedents) mentioned in the judgment that justify this plan."
}}

IMPORTANT: If outcome_for_government is 'WON', the action_type should be 'proceed_with_implementation' and you should focus on what the government can NOW do since the court has ruled in its favour. Do NOT recommend appealing when the government has won."""

# ── LLM Client ────────────────────────────────────────────────────────────────

class LLMService:
    def __init__(self):
        self.provider = settings.llm_provider
        self.timeout = httpx.Timeout(240.0, connect=10.0)

    async def health_check(self) -> bool:
        try:
            if self.provider == "ollama":
                async with httpx.AsyncClient(timeout=5.0) as client:
                    r = await client.get(f"{settings.ollama_base_url}/api/tags")
                    return r.status_code == 200
            elif self.provider == "openai":
                return bool(settings.openai_api_key)
            elif self.provider == "gemini":
                return bool(settings.gemini_api_key)
        except Exception:
            return False
        return False

    async def complete(self, system: str, user: str) -> str:
        if self.provider == "ollama":
            return await self._ollama_complete(system, user)
        elif self.provider == "openai":
            return await self._openai_complete(system, user)
        elif self.provider == "gemini":
            return await self._gemini_complete(system, user)
        raise ValueError(f"Unknown LLM provider: {self.provider}")

    async def _ollama_complete(self, system: str, user: str) -> str:
        payload = {
            "model": settings.ollama_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {
                "temperature": 0.05,   # Very low for consistent extraction
                "num_predict": 6000,
                "num_ctx": 16384,      # Use extended context
            },
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(
                f"{settings.ollama_base_url}/api/chat",
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
            return data["message"]["content"]

    async def _openai_complete(self, system: str, user: str) -> str:
        import openai
        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.05,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content

    async def _gemini_complete(self, system: str, user: str) -> str:
        import google.generativeai as genai
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(
            settings.gemini_model,
            system_instruction=system,
        )
        response = await model.generate_content_async(
            user,
            generation_config={"temperature": 0.05, "response_mime_type": "application/json"},
        )
        return response.text

    async def chat_with_document(self, document_text: str, messages: list[dict]) -> str:
        """Holistic chat with the document as context."""
        system_prompt = f"""You are a holistic, expert legal AI assistant designed to help government officials understand and act upon court judgments.
You have been provided with the full text of a court judgment.
Your goal is to answer questions accurately, reference specific parts of the text when possible, and provide actionable, clear, and professional advice.

CRITICAL INSTRUCTIONS:
1. ALWAYS use markdown formatting for readability (e.g., bullet points, **bold text**).
2. YOU MUST CITE YOUR SOURCES INLINE using the EXACT format `[Page X: "exact short quote"]`.
3. Every single factual sentence and every single bullet point you write MUST end with its corresponding `[Page X: "exact quote"]` tag.
4. DO NOT create a "Sources" or "References" list at the bottom of your response. All citations must be inline.

CORRECT FORMAT EXAMPLE:
Here is the timeline:
* On 08.01.2024, the Court treated the petition as public interest [Page 2: "public interest petition"].
* The committee rejected the application [Page 10: "rejected its application"].

INCORRECT FORMAT EXAMPLE (NEVER DO THIS):
Here is the timeline:
* On 08.01.2024, the Court treated the petition as public interest.
* The committee rejected the application.
Sources:
* [Page 2]
* [Page 10]

DOCUMENT CONTEXT:
{document_text}
"""
        
        # Prepare messages
        formatted_messages = [{"role": "system", "content": system_prompt}]
        for m in messages:
            # role should be "user" or "assistant"
            formatted_messages.append({"role": m["role"], "content": m["content"]})
            
        if self.provider == "ollama":
            payload = {
                "model": settings.ollama_model,
                "messages": formatted_messages,
                "stream": False,
                "options": {"temperature": 0.3, "num_ctx": 16384},
            }
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.post(f"{settings.ollama_base_url}/api/chat", json=payload)
                r.raise_for_status()
                return r.json()["message"]["content"]
        elif self.provider == "openai":
            import openai
            client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=formatted_messages,
                temperature=0.3,
            )
            return response.choices[0].message.content
        elif self.provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel(settings.gemini_model, system_instruction=system_prompt)
            # Gemini handles history slightly differently, but for simplicity we can construct a prompt
            # or use the chat session. Let's construct a prompt for simplicity if not using the chat session directly.
            # Actually, Gemini has chat sessions. For simplicity across providers, we'll format it as a single prompt if needed, 
            # or use Gemini's history format.
            gemini_history = []
            for m in messages[:-1]:
                role = "user" if m["role"] == "user" else "model"
                gemini_history.append({"role": role, "parts": [m["content"]]})
            
            chat = model.start_chat(history=gemini_history)
            response = await chat.send_message_async(messages[-1]["content"])
            return response.text
        
        raise ValueError(f"Unknown LLM provider: {self.provider}")


def _extract_json_from_response(text: str) -> dict:
    """Robustly extract JSON from LLM output that may have surrounding text/fences."""
    text = text.strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try markdown fence patterns
    for pattern in [
        r"```json\s*([\s\S]*?)\s*```",
        r"```\s*([\s\S]*?)\s*```",
        r"(\{[\s\S]*\})",
    ]:
        match = re.search(pattern, text)
        if match:
            candidate = match.group(1).strip()
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                # Try to fix common LLM JSON issues
                fixed = _fix_json(candidate)
                if fixed:
                    return fixed
                continue

    raise ValueError(f"Could not parse JSON from LLM response. First 300 chars:\n{text[:300]}")


def _fix_json(text: str) -> dict | None:
    """Attempt to fix common JSON issues from LLM output."""
    # Remove trailing commas before } or ]
    text = re.sub(r',\s*([}\]])', r'\1', text)
    # Fix unescaped quotes in values (rough heuristic)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _validate_extraction(data: dict) -> None:
    """Ensure required keys present, fill defaults."""
    list_keys = ["appellants", "respondents", "judges", "key_directions",
                 "relevant_laws", "government_departments"]
    for k in list_keys:
        if k not in data or not isinstance(data[k], list):
            data[k] = []

    scalar_keys = ["case_number", "court", "date_of_order", "outcome",
                   "outcome_for_government", "summary", "operative_order",
                   "compliance_deadline", "appeal_limitation_period",
                   "subject_matter", "stay_status", "responsible_department"]
    for k in scalar_keys:
        if k not in data:
            data[k] = None

    if "confidence_scores" not in data or not isinstance(data["confidence_scores"], dict):
        data["confidence_scores"] = {}
    if "source_quotes" not in data or not isinstance(data["source_quotes"], dict):
        data["source_quotes"] = {}
    if "source_pages" not in data or not isinstance(data["source_pages"], dict):
        data["source_pages"] = {}


def _validate_action_plan(data: dict) -> None:
    """Ensure required action plan keys present."""
    if "action_type" not in data:
        data["action_type"] = "seek_legal_opinion"
    if "priority" not in data:
        data["priority"] = "high"
    for key in ["critical_flags", "immediate_actions", "short_term_actions", "compliance_checklist", "compliance_timeline"]:
        if key not in data or not isinstance(data[key], list):
            data[key] = []
    if "appeal_assessment" not in data or not isinstance(data["appeal_assessment"], dict):
        data["appeal_assessment"] = {
            "should_appeal": False,
            "recommendation": "Seek legal opinion",
            "last_date": None,
        }
    if "departments_involved" not in data or not isinstance(data["departments_involved"], list):
        data["departments_involved"] = []


# ── Module-level singleton ────────────────────────────────────────────────────

llm_service = LLMService()


# ── High-level API ────────────────────────────────────────────────────────────

def _fix_government_outcome(data: dict) -> None:
    """
    Rule-based correction for government outcome.

    LLMs often confuse WHO won when an appeal is allowed.
    Logic:
    - Appeal Allowed + government is appellant  -> WON
    - Appeal Dismissed + government is appellant -> LOST
    - Petition Allowed + government is respondent -> LOST
    - Petition Dismissed + government is respondent -> WON
    - Stay vacated / impugned order set aside -> usually government appellant wins
    Only overrides if LLM gave a clearly contradictory answer.
    """
    outcome = (data.get("outcome") or "").lower()
    gov_party = (data.get("government_party") or "").lower()
    current = (data.get("outcome_for_government") or "").upper()

    # Appellant cases
    if gov_party == "appellant":
        if any(p in outcome for p in ["appeal allowed", "appeal is allowed", "allowed"]):
            if current != "WON":
                logger.info(f"Correcting outcome: {current} -> WON (appellant + appeal allowed)")
            data["outcome_for_government"] = "WON"
        elif any(p in outcome for p in ["appeal dismissed", "appeal is dismissed", "dismissed"]):
            if current != "LOST":
                logger.info(f"Correcting outcome: {current} -> LOST (appellant + appeal dismissed)")
            data["outcome_for_government"] = "LOST"

    # Respondent cases
    elif gov_party == "respondent":
        if any(p in outcome for p in ["petition allowed", "writ allowed", "allowed"]):
            if current != "LOST":
                logger.info(f"Correcting outcome: {current} -> LOST (respondent + petition allowed)")
            data["outcome_for_government"] = "LOST"
        elif any(p in outcome for p in ["petition dismissed", "writ dismissed", "dismissed"]):
            if current != "WON":
                logger.info(f"Correcting outcome: {current} -> WON (respondent + petition dismissed)")
            data["outcome_for_government"] = "WON"


def _build_smart_excerpt(full_text: str, max_chars: int = 14000) -> str:
    """
    For long judgments, take:
    - First 5000 chars (case header, parties, intro)
    - Last 4000 chars (operative order, final directions)
    - Middle sample (4000 chars) for factual background
    This gives the LLM the most decision-relevant parts.
    """
    if len(full_text) <= max_chars:
        return full_text

    head = full_text[:5000]
    tail = full_text[-4000:]
    mid_start = len(full_text) // 2 - 2000
    mid = full_text[mid_start: mid_start + 4000]

    return (
        head
        + "\n\n[... MIDDLE SECTION SUMMARIZED FOR CONTEXT ...]\n\n"
        + mid
        + "\n\n[... FINAL SECTION - OPERATIVE ORDER ...]\n\n"
        + tail
    )


async def extract_judgment_data(full_text: str) -> dict:
    """Extract structured data from judgment text using LLM."""
    text_to_use = _build_smart_excerpt(full_text)
    user_prompt = EXTRACTION_USER.format(text=text_to_use)

    try:
        response = await llm_service.complete(EXTRACTION_SYSTEM, user_prompt)
        logger.info(f"RAW EXTRACTION RESPONSE:\n{response}")
        data = _extract_json_from_response(response)
        _validate_extraction(data)
        _fix_government_outcome(data)   # Rule-based correction
        return data
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        raise


async def generate_action_plan(extraction_data: dict) -> dict:
    """Generate administrative action plan from extracted judgment data."""
    # Include only the most relevant fields for the action plan prompt
    relevant = {k: extraction_data.get(k) for k in [
        "case_number", "court", "date_of_order", "outcome",
        "outcome_for_government", "operative_order", "key_directions",
        "stay_status", "compliance_deadline", "appeal_limitation_period",
        "last_date_for_appeal", "next_proceedings", "government_party",
        "government_departments", "subject_matter", "summary"
    ]}

    user_prompt = ACTION_PLAN_USER.format(
        extraction_json=json.dumps(relevant, indent=2)
    )

    try:
        response = await llm_service.complete(ACTION_PLAN_SYSTEM, user_prompt)
        data = _extract_json_from_response(response)
        _validate_action_plan(data)
        return data
    except Exception as e:
        logger.error(f"Action plan generation failed: {e}")
        raise
