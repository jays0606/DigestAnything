"""Chat — streaming text chat with context awareness."""
import os

from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

CHAT_SYSTEM = """You are a helpful learning assistant. The user is studying this content:

Title: {title}
Key Concepts: {key_concepts}
Key Insights: {key_insights}

Rules:
- Answer in 2-4 sentences
- Use simple language
- Reference specific details from source
- If user asks to explain, include an analogy
- End with a follow-up question when appropriate"""


def build_system_prompt(context: dict) -> str:
    concepts = ", ".join([c["term"] for c in context.get("key_concepts", [])[:8]])
    insights = "; ".join(context.get("key_insights", [])[:4])
    return CHAT_SYSTEM.format(
        title=context.get("title", "Unknown"),
        key_concepts=concepts,
        key_insights=insights,
    )


_chat_histories: dict[str, list[str]] = {}


async def chat_response(message: str, session_id: str, context: dict) -> str:
    """Generate a chat response."""
    history = _chat_histories.setdefault(session_id, [])
    history.append(f"User: {message}")

    system_prompt = build_system_prompt(context)
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
    history.append(f"Assistant: {reply}")

    if len(history) > 20:
        _chat_histories[session_id] = history[-16:]

    return reply
