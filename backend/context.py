"""Context storage — save/load digested context to /tmp/digest/."""
import json
import os
import uuid

DIGEST_DIR = "/tmp/digest"


def ensure_dir():
    os.makedirs(DIGEST_DIR, exist_ok=True)


def new_session_id() -> str:
    return uuid.uuid4().hex[:12]


def save_context(session_id: str, context: dict) -> str:
    ensure_dir()
    path = os.path.join(DIGEST_DIR, f"context_{session_id}.json")
    with open(path, "w") as f:
        json.dump(context, f)
    return path


def load_context(session_id: str) -> dict | None:
    path = os.path.join(DIGEST_DIR, f"context_{session_id}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)
