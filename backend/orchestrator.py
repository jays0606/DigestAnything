"""Orchestrator — parallel pipeline after ingest."""
import asyncio

from visual import generate_markmap
from quiz import generate_quiz
from cards import generate_cards


async def run_pipeline(context: dict) -> dict:
    """Run all generation tasks in parallel after ingest.

    Returns dict with keys: markmap, quiz, cards, podcast
    """
    markmap, quiz, cards = await asyncio.gather(
        generate_markmap(context),
        generate_quiz(context),
        generate_cards(context),
    )

    return {
        "markmap": markmap,
        "quiz": quiz,
        "cards": cards,
    }
