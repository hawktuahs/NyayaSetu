# ⚖️ NyayaSetu — न्यायसेतु

**AI-Powered Court Judgment to Verified Action Plan System**  
*Theme 11 · AI for Bharat Hackathon*

> **NyayaSetu** (Justice Bridge) transforms complex court judgment PDFs into structured, human-verified action plans for government departments — using local AI with a mandatory human-in-the-loop.

---

## 🏗️ Architecture

```
Court Judgment PDF
       ↓
  FastAPI Backend  ──►  Ollama (LLaMA 3.1 8B)
       ↓                       ↓
  PDF Extraction          LLM Extraction
       ↓                       ↓
       └──────────────────────►│
                               ↓
                     AI Action Plan Generation
                               ↓
                   Human Verification Interface
                       (Approve / Edit / Reject)
                               ↓
                    Government Dashboard
                    (Verified Records Only)
```

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📄 **PDF Ingestion** | Multi-page PDF upload with drag-and-drop |
| 🤖 **AI Extraction** | LLaMA 3.1 extracts case details, directions, deadlines |
| 📋 **Action Plan** | AI generates comply/appeal/review plan with priority |
| 🔍 **Confidence Scores** | Per-field confidence for every extracted value |
| ✅ **Human Verification** | Side-by-side PDF + data view with inline editing |
| 📊 **Dashboard** | Approved records only, searchable and filterable |
| 🔄 **Auto-refresh** | Polling for extraction status updates |
| 🔌 **Multi-LLM** | Ollama (local), OpenAI, Gemini support |
| 💬 **Holistic Chatbot** | Document-aware Q&A for complex legal queries |
| 🎯 **Visual Highlighting** | Clickable citations jump to PDF + highlight source text |

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- [Ollama](https://ollama.ai) running locally with `llama3.1:8b`

```bash
# 1. Pull the LLM model
ollama pull llama3.1:8b

# 2. Start everything (Windows)
start.bat
```

### Manual Start

```bash
# Terminal 1: Backend
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## 🔌 LLM Configuration

Edit `backend/.env`:

```env
# Use Ollama (default, local)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Or switch to OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# Or switch to Gemini
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIza...
GEMINI_MODEL=gemini-1.5-pro
```

## 🧪 Running Tests

```bash
# Backend tests
cd backend
pip install -r requirements.txt
pytest tests/ -v

# Frontend (component tests)
cd frontend
npm test
```

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | LLM + system health check |
| `POST` | `/api/cases/upload` | Upload judgment PDF |
| `GET` | `/api/cases` | List all cases |
| `GET` | `/api/cases/{id}` | Get case + extraction + plan |
| `POST` | `/api/cases/{id}/retry` | Re-trigger extraction |
| `POST` | `/api/verify/{id}` | Submit verification decision |
| `GET` | `/api/verify/{id}/history` | Verification audit trail |
| `GET` | `/api/dashboard` | Approved cases (filterable) |
| `GET` | `/api/dashboard/stats` | Aggregate statistics |

Interactive docs: http://localhost:8000/docs

## 🗂️ Project Structure

```
NyayaSetu/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── config.py            # LLM + app configuration
│   ├── database.py          # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── services/
│   │   ├── pdf_service.py   # PyMuPDF extraction
│   │   └── llm_service.py   # LLM abstraction + prompts
│   ├── routers/
│   │   ├── cases.py         # Upload + extraction
│   │   ├── verification.py  # Human verification
│   │   └── dashboard.py     # Approved records
│   └── tests/
│       └── test_backend.py  # Full test suite
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Upload.jsx       # PDF upload
│       │   ├── CasesList.jsx    # All cases
│       │   ├── CaseDetail.jsx   # Case + extraction
│       │   ├── VerifyQueue.jsx  # Verification queue
│       │   ├── Verify.jsx       # Review interface
│       │   └── Dashboard.jsx    # Gov dashboard
│       ├── components/
│       │   ├── Navbar.jsx
│       │   ├── ConfidenceBadge.jsx
│       │   ├── FieldDisplay.jsx
│       │   └── StatusBadge.jsx
│       ├── api/client.js        # Axios API wrapper
│       └── store/index.js       # Zustand state
├── sample_judgments/            # Demo PDFs
├── create_sample_pdf.py         # Sample PDF generator
├── start.bat                    # One-click startup (Windows)
└── README.md
```

## 🔐 Data Flow & Trust Model

```
Upload → Extract → AI Action Plan
                       ↓
             [MANDATORY HUMAN REVIEW]
               ✏️ Edit if needed
               ✅ Approve → Dashboard
               ❌ Reject → Archive
```

Only **human-approved** records appear on the dashboard. The AI is a decision-support tool, not an autonomous actor.

## 🧠 AI Prompt Engineering

The LLM is given two structured prompts:

1. **Extraction Prompt** — Extracts 10 structured fields with per-field confidence scores (0–1)
2. **Action Plan Prompt** — Generates comply/appeal/review recommendation with stepped action plan

Both prompts enforce JSON-only output and use temperature=0.1 for consistency.

## 📊 Evaluation Alignment

| Criteria | Implementation |
|----------|---------------|
| Extraction accuracy | Confidence scores + retry mechanism |
| Action plan quality | Structured steps with priority + risk assessment |
| Human verification | Side-by-side PDF, inline edit, audit trail |
| Dashboard clarity | Search, filter, priority sort, expandable summaries |
| Complex PDFs | PyMuPDF + text truncation + scanned PDF detection |
| Explainability | Confidence bars + AI reasoning field |

---

*Built for AI for Bharat Hackathon — Theme 11: From Court Judgments to Verified Action Plans*
