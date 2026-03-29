"""Visual — context hierarchy → markmap markdown."""
import json

from google import genai
from google.genai import types

import os

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

MARKMAP_PROMPT = """Convert this hierarchy into a markdown outline for a mindmap.

RULES:
- # for main topic
- ## for major branches (3-5 max)
- ### for sub-concepts
- Bullet points (-) for 1-sentence leaf details
- Keep labels under 5 words
- Use emoji prefixes for key nodes
- Max 3 heading levels, 10-15 nodes total

INPUT: {hierarchy}

OUTPUT: Markdown only. No backticks. Start with #."""


async def generate_markmap(context: dict) -> str:
    """Generate markmap markdown from context hierarchy."""
    hierarchy = context.get("hierarchy", {})
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=MARKMAP_PROMPT.format(hierarchy=json.dumps(hierarchy)),
        config=types.GenerateContentConfig(
            temperature=1.0,
            thinking_config=types.ThinkingConfig(thinking_level="LOW"),
        ),
    )
    return response.text
