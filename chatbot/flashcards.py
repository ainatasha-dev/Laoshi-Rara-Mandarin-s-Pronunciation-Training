"""Flashcard decks loaded from UITM textbook vocabulary."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "textbook_vocab.json"


@dataclass
class Flashcard:
    id: str
    chinese: str
    pinyin: str
    english: str
    malay: str
    note: str = ""
    deck: str = "general"


def _load_textbook_data() -> dict:
    if not DATA_PATH.exists():
        return {"decks": {}}
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def _build_decks() -> dict[str, list[Flashcard]]:
    raw = _load_textbook_data()
    decks: dict[str, list[Flashcard]] = {}
    for deck_id, deck_data in raw.get("decks", {}).items():
        cards = []
        for item in deck_data.get("cards", []):
            cards.append(
                Flashcard(
                    id=item["id"],
                    chinese=item.get("chinese", ""),
                    pinyin=item.get("pinyin", ""),
                    english=item.get("english", ""),
                    malay=item.get("malay", ""),
                    note=item.get("note", ""),
                    deck=deck_id,
                )
            )
        decks[deck_id] = cards
    return decks


FLASHCARD_DECKS: dict[str, list[Flashcard]] = _build_decks()

DECK_TITLES: dict[str, str] = {}
_raw = _load_textbook_data()
for _deck_id, _deck_data in _raw.get("decks", {}).items():
    DECK_TITLES[_deck_id] = _deck_data.get("title", _deck_id)


def textbook_source() -> str:
    return _raw.get("source", "Textbook vocabulary")


def all_decks() -> dict[str, str]:
    return DECK_TITLES.copy()


def get_deck(deck_id: str) -> list[Flashcard]:
    return FLASHCARD_DECKS.get(deck_id, [])
