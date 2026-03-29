"""FastAPI app — routes + CORS + static mount."""
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from context import save_context, load_context, new_session_id, ensure_dir
from ingest import fetch_source_text, analyze
from visual import generate_markmap
from quiz import generate_quiz
from cards import generate_cards
from chat import chat_response
from tutor import tutor_response
from orchestrator import run_pipeline

app = FastAPI(title="DigestAnything API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for podcast audio
ensure_dir()
app.mount("/static", StaticFiles(directory="/tmp/digest"), name="static")


# --- Request models ---

class IngestRequest(BaseModel):
    source: str


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class TutorRequest(BaseModel):
    message: str
    session_id: str = "default"
    concept: str | None = None


# --- Routes ---

@app.post("/api/ingest")
async def api_ingest(req: IngestRequest):
    """Parse source → Gemini analysis → structured context."""
    source_text = await fetch_source_text(req.source)
    if not source_text or len(source_text) < 50:
        raise HTTPException(status_code=400, detail="Could not extract text from source")
    context = await analyze(source_text)
    session_id = new_session_id()
    context["session_id"] = session_id
    save_context(session_id, context)
    return context


@app.post("/api/visual")
async def api_visual(context: dict):
    """Context → markmap markdown."""
    markdown = await generate_markmap(context)
    return {"markdown": markdown}


@app.get("/api/context/{session_id}")
async def api_context(session_id: str):
    """Retrieve stored context."""
    ctx = load_context(session_id)
    if ctx is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return ctx


@app.post("/api/quiz")
async def api_quiz(context: dict):
    """Context → 10 MCQ questions."""
    result = await generate_quiz(context)
    return result


@app.post("/api/cards")
async def api_cards(context: dict):
    """Context → 12-15 flashcards."""
    result = await generate_cards(context)
    return result


@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    """Streaming text chat."""
    ctx = load_context(req.session_id)
    if ctx is None:
        ctx = {"title": "General", "key_concepts": [], "key_insights": []}
    reply = await chat_response(req.message, req.session_id, ctx)
    return {"response": reply}


@app.post("/api/tutor")
async def api_tutor(req: TutorRequest):
    """Socratic tutor."""
    ctx = load_context(req.session_id)
    if ctx is None:
        ctx = {"title": "General", "key_concepts": [], "key_insights": [], "analogies": []}
    reply = await tutor_response(req.message, req.session_id, ctx, req.concept)
    return {"response": reply}


@app.post("/api/digest")
async def api_digest(req: IngestRequest):
    """Full pipeline: ingest → parallel generation."""
    source_text = await fetch_source_text(req.source)
    if not source_text or len(source_text) < 50:
        raise HTTPException(status_code=400, detail="Could not extract text from source")
    context = await analyze(source_text)
    session_id = new_session_id()
    context["session_id"] = session_id
    save_context(session_id, context)

    pipeline = await run_pipeline(context)

    return {
        "context": context,
        "markmap": pipeline.get("markmap"),
        "quiz": pipeline.get("quiz"),
        "cards": pipeline.get("cards"),
        "podcast": pipeline.get("podcast"),
    }
