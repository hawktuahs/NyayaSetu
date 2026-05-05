"""NyayaSetu — FastAPI Application"""
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from database import init_db, Case, get_db
from services.llm_service import llm_service
from schemas import HealthResponse
from sqlalchemy import select

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("NyayaSetu starting up...")
    await init_db()
    ok = await llm_service.health_check()
    logger.info(f"LLM ready: {settings.llm_provider} / {getattr(settings, f'{settings.llm_provider}_model', '?')}" if ok else "LLM NOT available")
    yield
    logger.info("NyayaSetu shutting down")


app = FastAPI(
    title="NyayaSetu API",
    description="AI-powered court judgment to verified action plan system",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
from routers import cases, verification, dashboard
app.include_router(cases.router)
app.include_router(verification.router)
app.include_router(dashboard.router)


# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/api/health", response_model=HealthResponse, tags=["system"])
async def health():
    ok = await llm_service.health_check()
    model_key = f"{settings.llm_provider}_model"
    return HealthResponse(
        status="ok",
        llm_provider=settings.llm_provider,
        llm_model=getattr(settings, model_key, settings.ollama_model),
        llm_available=ok,
        database="sqlite (async)",
    )


# ── PDF serving ────────────────────────────────────────────────────────────────
@app.get("/api/cases/{case_id}/pdf", tags=["cases"])
async def serve_pdf(case_id: int):
    """Serve the uploaded PDF directly for inline viewing."""
    from database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Case).where(Case.id == case_id))
        case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "Case not found")
    p = Path(case.pdf_path)
    if not p.exists():
        raise HTTPException(404, "PDF file not found on disk")
    from fastapi import Response
    content = p.read_bytes()
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline"}
    )


# ── Serve React SPA (production) ───────────────────────────────────────────────
_frontend = Path(__file__).parent.parent / "frontend" / "dist"
if _frontend.exists():
    app.mount("/assets", StaticFiles(directory=str(_frontend / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa(full_path: str):
        return FileResponse(str(_frontend / "index.html"))
