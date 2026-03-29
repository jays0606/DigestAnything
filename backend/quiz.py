"""Quiz — context → 10 MCQ questions."""
import json
import os

from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

QUIZ_PROMPT = """Generate 10 multiple-choice questions testing deep understanding.

DIFFICULTY:
- Q1-3: Easy (recall, basic definitions)
- Q4-7: Medium (application, "what would happen if...")
- Q8-9: Hard (synthesis, edge cases)
- Q10: Expert (connect multiple concepts)

PER QUESTION:
- 4 options (A, B, C, D)
- Wrong answers must be plausible (common misconceptions)
- "correct": index 0-3
- "explanation": 2-3 sentences
- At least 2 scenario questions
- At least 1 relationship question
- Test UNDERSTANDING not memorization"""

QUIZ_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "questions": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "INTEGER"},
                    "difficulty": {"type": "STRING", "enum": ["easy", "medium", "hard", "expert"]},
                    "question": {"type": "STRING"},
                    "options": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "correct": {"type": "INTEGER"},
                    "explanation": {"type": "STRING"},
                },
                "required": ["id", "difficulty", "question", "options", "correct", "explanation"],
            },
        },
    },
    "required": ["questions"],
}


async def generate_quiz(context: dict) -> dict:
    """Generate 10 MCQ questions from context."""
    import asyncio

    def _call():
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[json.dumps(context), QUIZ_PROMPT],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=QUIZ_SCHEMA,
                temperature=1.0,
                thinking_config=types.ThinkingConfig(thinking_level="LOW"),
            ),
        )
        return json.loads(response.text)

    return await asyncio.to_thread(_call)
