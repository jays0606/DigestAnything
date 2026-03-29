"""Orchestrator — parallel pipeline after ingest."""
import asyncio

from visual import generate_markmap


async def run_pipeline(context: dict) -> dict:
    """Run all generation tasks in parallel after ingest.

    Returns dict with keys: markmap, quiz, cards, podcast
    Currently only markmap is implemented (Round 1).
    """
    markmap_task = asyncio.create_task(generate_markmap(context))

    # Future rounds will add more tasks here via asyncio.gather()
    markmap = await markmap_task

    return {
        "markmap": markmap,
    }
