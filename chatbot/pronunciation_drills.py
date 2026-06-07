"""Pronunciation drill items for Laoshi Rara — from textbook & lessons."""

from __future__ import annotations

from chatbot.lessons import LESSONS

# Tone number from pinyin tone marks
_TONE_MAP = {
    "ā": 1, "á": 2, "ǎ": 3, "à": 4,
    "ē": 1, "é": 2, "ě": 3, "è": 4,
    "ī": 1, "í": 2, "ǐ": 3, "ì": 4,
    "ō": 1, "ó": 2, "ǒ": 3, "ò": 4,
    "ū": 1, "ú": 2, "ǔ": 3, "ù": 4,
    "ǖ": 1, "ǘ": 2, "ǚ": 3, "ǜ": 4,
}


def tone_from_pinyin(pinyin: str) -> int | None:
    for char in pinyin:
        if char in _TONE_MAP:
            return _TONE_MAP[char]
    return None


def _drill(
    drill_id: str,
    word: str,
    pinyin: str,
    english: str,
    malay: str,
    note: str = "",
) -> dict:
    return {
        "id": drill_id,
        "word": word,
        "pinyin": pinyin,
        "english": english,
        "malay": malay,
        "note": note,
        "expected_tone": tone_from_pinyin(pinyin),
        "label": f"{pinyin} — {english}",
    }


NUMBER_DRILLS_1_10: list[dict] = [
    _drill("num_1", "一", "yī", "one", "satu", "Tone 1 — high flat"),
    _drill("num_2", "二", "èr", "two", "dua", "Tone 4 — falling"),
    _drill("num_3", "三", "sān", "three", "tiga", "Tone 1 — high flat"),
    _drill("num_4", "四", "sì", "four", "empat", "Tone 4 — falling"),
    _drill("num_5", "五", "wǔ", "five", "lima", "Tone 3 — dipping"),
    _drill("num_6", "六", "liù", "six", "enam", "Tone 4 — falling"),
    _drill("num_7", "七", "qī", "seven", "tujuh", "Tone 1 — high flat"),
    _drill("num_8", "八", "bā", "eight", "lapan", "Tone 1 — high flat"),
    _drill("num_9", "九", "jiǔ", "nine", "sembilan", "Tone 3 — dipping"),
    _drill("num_10", "十", "shí", "ten", "sepuluh", "Tone 2 — rising"),
]

TONE_DRILLS: list[dict] = [
    _drill("tone_ma1", "妈", "mā", "mother", "emak", "Tone 1 — high flat"),
    _drill("tone_ma2", "麻", "má", "hemp", "hem", "Tone 2 — rising"),
    _drill("tone_ma3", "马", "mǎ", "horse", "kuda", "Tone 3 — dipping"),
    _drill("tone_ma4", "骂", "mà", "to scold", "memarahi", "Tone 4 — falling"),
]


def _lesson_drills() -> list[dict]:
    drills: list[dict] = []
    for lesson in LESSONS.values():
        for step in lesson["steps"]:
            target = step.get("speak_target")
            if not target:
                continue
            pinyin = target.get("pinyin", "")
            drills.append(
                {
                    "id": step["id"],
                    "word": target.get("word", ""),
                    "pinyin": pinyin,
                    "english": target.get("english", ""),
                    "malay": target.get("malay", ""),
                    "note": target.get("note", ""),
                    "expected_tone": target.get("expected_tone") or tone_from_pinyin(pinyin),
                    "label": f"{pinyin} — {target.get('english', '')}",
                }
            )
    return drills


def _textbook_greeting_drills() -> list[dict]:
    """Key single-word drills from textbook (greetings & polite)."""
    items = [
        ("tb_nihao", "你好", "nǐ hǎo", "hello", "selamat sejahtera", "Tone 3 + Tone 3"),
        ("tb_xiexie", "谢谢", "xièxie", "thank you", "terima kasih", "Tone 4 + neutral"),
        ("tb_zaoshanghao", "早上好", "zǎoshang hǎo", "good morning", "selamat pagi", "Mixed tones"),
        ("tb_zaijian", "再见", "zàijiàn", "goodbye", "jumpa lagi", "Tone 4 + Tone 4"),
    ]
    return [_drill(*row) for row in items]


PRONUNCIATION_CATEGORIES: dict[str, dict] = {
    "numbers_1_10": {
        "title": "Numbers 1–10 (数字)",
        "drills": NUMBER_DRILLS_1_10,
    },
    "four_tones": {
        "title": "Four Tones — mā má mǎ mà",
        "drills": TONE_DRILLS,
    },
    "greetings": {
        "title": "Greetings & Polite Words",
        "drills": _textbook_greeting_drills(),
    },
    "lesson_words": {
        "title": "Lesson Practice Words",
        "drills": _lesson_drills(),
    },
}


def list_categories() -> dict[str, str]:
    return {key: cat["title"] for key, cat in PRONUNCIATION_CATEGORIES.items()}


def get_drills(category: str) -> list[dict]:
    return PRONUNCIATION_CATEGORIES.get(category, {}).get("drills", [])
