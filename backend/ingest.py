"""Source ingestion — URL/YouTube/PDF → Gemini → structured context JSON."""
import json
import re

from google import genai
from google.genai import types
import trafilatura
from youtube_transcript_api import YouTubeTranscriptApi

import os

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

ANALYSIS_PROMPT = """You are a world-class learning content designer.

Analyze the provided content and extract a structured learning context.

RULES:
- Generate exactly 10-15 key_concepts
- Generate exactly 3-5 hierarchy children with 2-4 children each
- Generate exactly 3-5 key_insights
- Generate exactly 2-4 analogies
- Definitions understandable by a smart 16-year-old
- Hierarchy labels SHORT (3-5 words) — they render as mindmap nodes
- Insights should make someone say "oh interesting"
"""

ANALYSIS_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"},
        "subtitle": {"type": "STRING"},
        "summary": {"type": "STRING"},
        "difficulty": {"type": "STRING", "enum": ["beginner", "intermediate", "advanced"]},
        "estimated_read_time_minutes": {"type": "INTEGER"},
        "key_concepts": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "term": {"type": "STRING"},
                    "definition": {"type": "STRING"},
                    "importance": {"type": "STRING", "enum": ["high", "medium"]},
                    "related_to": {"type": "ARRAY", "items": {"type": "STRING"}},
                },
                "required": ["term", "definition", "importance", "related_to"],
            },
        },
        "hierarchy": {
            "type": "OBJECT",
            "properties": {
                "root": {"type": "STRING"},
                "children": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "name": {"type": "STRING"},
                            "children": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "description": {"type": "STRING"},
                        },
                        "required": ["name", "children", "description"],
                    },
                },
            },
            "required": ["root", "children"],
        },
        "key_insights": {"type": "ARRAY", "items": {"type": "STRING"}},
        "analogies": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "concept": {"type": "STRING"},
                    "analogy": {"type": "STRING"},
                    "explanation": {"type": "STRING"},
                },
                "required": ["concept", "analogy", "explanation"],
            },
        },
    },
    "required": ["title", "subtitle", "summary", "difficulty", "estimated_read_time_minutes", "key_concepts", "hierarchy", "key_insights", "analogies"],
}


def extract_youtube_id(url: str) -> str | None:
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


async def fetch_source_text(source: str) -> str:
    """Extract text from URL, YouTube, or raw text."""
    # YouTube
    vid_id = extract_youtube_id(source)
    if vid_id:
        ytt = YouTubeTranscriptApi()
        transcript = ytt.fetch(vid_id, languages=["en", "ko"])
        return " ".join([t.text for t in transcript])

    # Web URL
    if source.startswith("http"):
        html = trafilatura.fetch_url(source)
        if html:
            text = trafilatura.extract(html)
            if text:
                return text

    # Raw text fallback
    return source


async def analyze(source_text: str) -> dict:
    """Run Gemini analysis on source text → structured context."""
    import asyncio

    def _call():
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[source_text, ANALYSIS_PROMPT],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ANALYSIS_SCHEMA,
                temperature=1.0,
                thinking_config=types.ThinkingConfig(thinking_level="LOW"),
            ),
        )
        return json.loads(response.text)

    return await asyncio.to_thread(_call)
