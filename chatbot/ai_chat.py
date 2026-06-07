"""OpenAI-powered chat for Laoshi Rara (Cikgu Bot style)."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from chatbot.laoshi_persona import LAOSHI_PERSONA, TOPIC_FOCUS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / "app.env")
load_dotenv(PROJECT_ROOT / ".env")

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_HISTORY = 12


def _client() -> OpenAI | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def _extract_text(response) -> str:
    try:
        return response.choices[0].message.content.strip()
    except Exception:
        return ""


def build_system_prompt(topic_key: str = "General") -> str:
    extra = TOPIC_FOCUS.get(topic_key, "")
    if extra:
        return f"{LAOSHI_PERSONA}\n\n## Session focus\n{extra}"
    return LAOSHI_PERSONA


def generate_laoshi_reply(
    user_input: str,
    history: list[dict],
    topic_key: str = "General",
) -> tuple[str, str | None]:
    """
    Returns (assistant_reply, error_message).
    history items: {"role": "user"|"assistant", "content": str}
    """
    client = _client()
    if client is None:
        return (
            "",
            "OpenAI API key missing. Add OPENAI_API_KEY to app.env in the project folder.",
        )

    messages = [{"role": "system", "content": build_system_prompt(topic_key)}]
    messages.extend(history[-MAX_HISTORY:])
    messages.append({"role": "user", "content": user_input})

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=350,
            temperature=0.5,
        )
        text = _extract_text(response)
        if not text:
            return "", "Laoshi Rara could not generate a reply. Please try again."
        return text, None
    except Exception as exc:
        return "", f"Connection problem: {exc}. Please try again."


def api_key_configured() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))
