# NyayaSetu (Justice Bridge)

NyayaSetu automates the heavy lifting of administrative legal compliance. Simply upload a court judgment document (PDF), and the system's AI pipeline instantly deconstructs it into structured data. It extracts mandatory directives, critical deadlines, involved parties, and the final outcome. Once the judgment is parsed, the AI autonomously generates a structured, verifiable administrative action plan, ensuring no court order slips through the cracks.

## Key Features

- **Deep Judgment Analysis:** Automatically extracts structured metadata, including case numbers, judges, bench types, operative orders, and compliance deadlines from unstructured legal PDFs.
- **Automated Action Planning:** Intelligently assesses the outcome (Won/Lost/Partial) and generates a stepped action plan (e.g., Proceed with Implementation, File Appeal, Seek Legal Opinion) with assigned priority levels.
- **Human-in-the-Loop AI:** Employs confidence scores for every extracted data point. Ambiguous extractions are flagged for human review in a side-by-side validation interface, ensuring critical government decisions are never left entirely to the machine.
- **Interactive Q&A (Document Chatbot):** A "Legal AI Assistant" allows reviewers to query the dense judgment document in natural language and receive instant, grounded answers with interactive citations that highlight the source text directly in the PDF viewer.
- **Verifiable Audit Trail:** Every AI-generated plan must be explicitly approved, edited, or rejected by a designated official, creating a secure chain of accountability.
- **100% Private & Local-Ready:** Built to run entirely locally using Ollama. Sensitive government legal documents never have to leave the host machine, ensuring absolute data sovereignty.

## Tech Stack

- **Frontend:** React, Vite, Vanilla CSS (Modern, responsive, glassmorphism UI)
- **Backend:** FastAPI, Python, SQLAlchemy/SQLite (Robust, async API)
- **AI Engine:** Local LLMs via Ollama (Llama 3.1 8B), with abstractions to plug into OpenAI/Gemini if cloud scaling is desired.
- **Document Processing:** PyMuPDF for resilient text extraction from complex and scanned legal PDFs.

## How It Works

| Step | Action | What the AI Does |
| :--- | :--- | :--- |
| **1. Parse** | Upload Judgment PDF | Extracts mandatory directions, case details, and deadlines. *(Takes ~1-2 minutes locally depending on document size)* |
| **2. Plan** | Generate Action Plan | Reads the operative order and proposes a compliance or appeal strategy with urgency ratings. |
| **3. Review** | Human Oversight | Presents the extraction side-by-side with the PDF. A human verifies the data and approves the plan. |
| **4. Execute** | Government Dashboard | Spits out a clean, actionable record to a centralized dashboard for immediate departmental execution. |

In the realm of government administration, accountability and data security are non-negotiable. NyayaSetu delivers a verifiable AI pipeline. Every extraction and action plan includes a confidence score, reasoning, and direct interactive citations to the source text. By supporting local execution, we eliminate the data privacy risks associated with cloud-based AI, offering a powerful, enterprise-grade tool that bridges the gap between court orders and government action.

---

## 📊 Prompt to Generate a PowerPoint Presentation

*Copy and paste the prompt below into ChatGPT, Claude, or a presentation generator like Gamma.app to create your pitch deck.*

> **Prompt:**
> "Act as an expert startup founder and presentation designer. I need you to create the content and slide outline for a 10-slide pitch deck for a project called **NyayaSetu (Justice Bridge)**. 
> 
> **Context:** NyayaSetu is an AI-powered platform designed for the government. It takes complex, unstructured court judgment PDFs and automatically extracts key directives, deadlines, and outcomes. It then generates a prioritized 'Action Plan' (e.g., comply, appeal) for government departments. It features a Human-in-the-Loop verification UI, a holistic Document Chatbot that highlights source text in the PDF, and it runs 100% locally using Ollama for total data privacy.
> 
> Please structure the deck as follows, providing the Title, Key Bullet Points, and a Visual Suggestion for each slide:
> 
> 1. **Title Slide:** Name and 1-sentence hook.
> 2. **The Problem:** Government departments miss court deadlines due to dense, unstructured PDF judgments, leading to contempt of court.
> 3. **The Solution:** NyayaSetu – Automated extraction and action planning.
> 4. **How It Works (The Pipeline):** Parse -> Plan -> Review -> Execute.
> 5. **Key Features:** Deep analysis, Automated Planning, Local AI.
> 6. **Human-in-the-Loop:** Emphasize that AI proposes, but Humans verify (confidence scores, side-by-side UI).
> 7. **Interactive Document Chatbot:** The RAG feature that allows users to 'chat' with the judgment and click citations to highlight the PDF.
> 8. **Privacy & Tech Stack:** FastAPI, React, PyMuPDF, and Local Llama 3.1 8B (Zero data leaks).
> 9. **Impact:** Faster compliance, zero missed deadlines, reduced legal costs.
> 10. **Conclusion/Call to Action:** Ready for deployment.
> 
> Keep the text on the slides punchy, professional, and persuasive. Use bolding for emphasis."
