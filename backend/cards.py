"""Cards — context → 12-15 flashcards."""
import json
import os

from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

CARDS_PROMPT = """Generate 12-15 flashcards for spaced repetition.

CARD TYPES (mix):
- Definition (6-8): Term → definition + example
- Comparison (2-3): "X vs Y" → key differences
- Application (2-3): Scenario → correct approach

RULES:
- Front: 1-6 words max
- Back: 2-3 sentences max. Self-contained.
- Order: foundational → advanced"""

CARDS_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "cards": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "front": {"type": "STRING"},
                    "back": {"type": "STRING"},
                    "type": {"type": "STRING", "enum": ["definition", "comparison", "application"]},
                },
                "required": ["front", "back", "type"],
            },
        },
    },
    "required": ["cards"],
}


async def generate_cards(context: dict) -> dict:
    """Generate 12-15 flashcards from context."""
    import asyncio

    def _call():
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[json.dumps(context), CARDS_PROMPT],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CARDS_SCHEMA,
                temperature=1.0,
                thinking_config=types.ThinkingConfig(thinking_level="LOW"),
            ),
        )
        return json.loads(response.text)

    return await asyncio.to_thread(_call)
