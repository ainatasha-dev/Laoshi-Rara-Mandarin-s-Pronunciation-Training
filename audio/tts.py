"""Text-to-speech for Chinese, pinyin, English, and Malay."""

from __future__ import annotations

import asyncio
import re

VOICES = {
    "chinese": "zh-CN-XiaoxiaoNeural",
    "pinyin": "en-US-JennyNeural",
    "english": "en-US-JennyNeural",
    "malay": "ms-MY-YasminNeural",
}


def _strip_tone_marks(pinyin: str) -> str:
    """Convert toned pinyin to plain ASCII for clearer TTS pronunciation."""
    normalized = pinyin
    replacements = {
        "ā": "a", "á": "a", "ǎ": "a", "à": "a",
        "ē": "e", "é": "e", "ě": "e", "è": "e",
        "ī": "i", "í": "i", "ǐ": "i", "ì": "i",
        "ō": "o", "ó": "o", "ǒ": "o", "ò": "o",
        "ū": "u", "ú": "u", "ǔ": "u", "ù": "u",
        "ǖ": "v", "ǘ": "v", "ǚ": "v", "ǜ": "v", "ü": "v",
    }
    for src, dst in replacements.items():
        normalized = normalized.replace(src, dst)
    normalized = re.sub(r"[^\w\s'-]", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


async def _generate_audio_bytes(text: str, voice: str) -> bytes:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    chunks: list[bytes] = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            chunks.append(chunk["data"])
    return b"".join(chunks)


def text_to_speech_bytes(text: str, language: str) -> bytes | None:
    """Generate MP3 bytes for the given language key."""
    if not text or not text.strip():
        return None

    voice = VOICES.get(language)
    if not voice:
        return None

    spoken = text.strip()
    if language == "pinyin":
        spoken = _strip_tone_marks(spoken)

    if not spoken:
        return None

    return asyncio.run(_generate_audio_bytes(spoken, voice))
