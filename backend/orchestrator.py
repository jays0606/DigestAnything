"""Orchestrator — parallel pipeline after ingest."""
import asyncio

from visual import generate_markmap
from quiz import generate_quiz
from cards import generate_cards
from podcast import generate_podcast


async def run_pipeline(context: dict) -> dict:
    """Run all generation tasks in parallel after ingest."""
    session_id = context.get("session_id", "default")

    markmap, quiz, cards, podcast = await asyncio.gather(
        generate_markmap(context),
        generate_quiz(context),
        generate_cards(context),
        generate_podcast(context, session_id),
    )

    return {
        "markmap": markmap,
        "quiz": quiz,
        "cards": cards,
        "podcast": podcast,
    }
