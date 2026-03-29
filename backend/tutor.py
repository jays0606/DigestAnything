"""Tutor — Socratic Feynman technique tutor."""
import os

from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

TUTOR_SYSTEM = """You are Sage, a Socratic tutor using the Feynman Technique.

The student is learning: {title}
Concepts: {key_concepts}
Analogies: {analogies}

WHEN STUDENT ASKS A QUESTION:
- Answer in 2-3 sentences with an analogy
- End with a deeper follow-up question

WHEN STUDENT TRIES TO EXPLAIN:
- First: praise what they got right (1 sentence)
- Then: identify the SPECIFIC gap
- Ask ONE probing question about the gap
- NEVER give the full answer directly
- When they nail it: "Yes! And here's one more thing..."

RESPONSE RULES:
- Keep responses under 80 words
- Conversational: "So...", "Right, here's the thing..."
- Warm and encouraging, not lecturing
- Don't give hints too easily — let the brain sweat

NEVER:
- Give long lectures
- Say "that's wrong" without saying what's right
- Use jargon without defining it"""


def build_tutor_system(context: dict) -> str:
    concepts = ", ".join([c["term"] for c in context.get("key_concepts", [])[:8]])
    analogies = "; ".join([f"{a['concept']} is like {a['analogy']}" for a in context.get("analogies", [])[:4]])
    return TUTOR_SYSTEM.format(
        title=context.get("title", "Unknown"),
        key_concepts=concepts,
        analogies=analogies,
    )


_tutor_histories: dict[str, list[str]] = {}


async def tutor_response(message: str, session_id: str, context: dict, concept: str | None = None) -> str:
    """Generate a Socratic tutor response."""
    history = _tutor_histories.setdefault(session_id, [])

    full_message = message
    if concept:
        full_message = f"[Focusing on: {concept}] {message}"

    history.append(f"Student: {full_message}")

    system_prompt = build_tutor_system(context)
    conversation = "\n".join(history)

    import asyncio

    def _call():
        return client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=conversation,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=1.0,
                thinking_config=types.ThinkingConfig(thinking_level="LOW"),
            ),
        )

    response = await asyncio.to_thread(_call)
    reply = response.text
    history.append(f"Sage: {reply}")

    if len(history) > 20:
        _tutor_histories[session_id] = history[-16:]

    return reply
