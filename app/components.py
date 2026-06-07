"""Streamlit UI helpers for Laoshi Rara."""

from __future__ import annotations

import base64
import json
import time
from pathlib import Path

import streamlit as st

from audio.tts import text_to_speech_bytes
from chatbot.flashcards import Flashcard, all_decks, get_deck
from chatbot.pronunciation_drills import get_drills, list_categories

NOTES_PATH = Path(__file__).resolve().parents[1] / "data" / "user_notes.json"

LAOSHI_AVATAR = "👩‍🏫"
STUDENT_AVATAR = "🧑‍🎓"


@st.cache_data(show_spinner=False)
def cached_speech(text: str, language: str) -> bytes | None:
    return text_to_speech_bytes(text, language)


def load_user_notes() -> dict[str, str]:
    if not NOTES_PATH.exists():
        return {}
    try:
        return json.loads(NOTES_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_user_notes(notes: dict[str, str]) -> None:
    NOTES_PATH.parent.mkdir(parents=True, exist_ok=True)
    NOTES_PATH.write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8")


def play_audio_now(audio: bytes) -> None:
    """Play immediately on button click — new token each time so repeat clicks work."""
    token = time.time_ns()
    b64 = base64.b64encode(audio).decode()
    st.components.v1.html(
        f"""
        <audio id="player{token}" autoplay>
            <source src="data:audio/mpeg;base64,{b64}" type="audio/mpeg">
        </audio>
        <script>
            const audio = document.getElementById("player{token}");
            if (audio) {{ audio.play().catch(function() {{}}); }}
        </script>
        """,
        height=0,
    )


def render_speak_buttons(
    chinese: str = "",
    english: str = "",
    malay: str = "",
    key_prefix: str = "tts",
) -> None:
    options = [
        ("english", "English", english),
        ("malay", "Malay", malay),
        ("chinese", "Mandarin", chinese),
    ]
    active = [(lang, label, text) for lang, label, text in options if text and text.strip()]
    if not active:
        return

    cols = st.columns(len(active))
    for col, (lang, label, text) in zip(cols, active):
        with col:
            if st.button(f"🔊 {label}", key=f"{key_prefix}_{lang}", use_container_width=True):
                with st.spinner("Loading..."):
                    audio = cached_speech(text, lang)
                if audio:
                    play_audio_now(audio)
                else:
                    st.warning(f"Could not play {label}.")


def render_ai_chat_message(message: dict, *, show_listen: bool = False) -> None:
    """Render one turn from OpenAI chat history."""
    role = message.get("role", "assistant")
    content = message.get("content", "")

    if role == "user":
        with st.chat_message("Student", avatar=STUDENT_AVATAR):
            st.write(content)
        return

    with st.chat_message("Laoshi Rara", avatar=LAOSHI_AVATAR):
        st.write(content)
        if show_listen:
            render_speak_buttons(
                english=content,
                key_prefix=f"ai_{abs(hash(content)) % 999999}",
            )


def render_chat_message(message, *, show_listen: bool = False) -> None:
    if message.role == "user":
        with st.chat_message("Student", avatar=STUDENT_AVATAR):
            st.write(message.content)
        return

    meta = message.meta or {}
    text = meta.get("english") or message.content

    with st.chat_message("Laoshi Rara", avatar=LAOSHI_AVATAR):
        st.write(text)
        if meta.get("pinyin"):
            st.caption(f"Pinyin: {meta['pinyin']}")
        if meta.get("malay"):
            st.caption(f"Malay: {meta['malay']}")

        if show_listen and meta.get("type") == "prompt":
            render_speak_buttons(
                chinese=meta.get("chinese", ""),
                english=meta.get("english", ""),
                malay=meta.get("malay", ""),
                key_prefix=f"msg_{abs(hash(text)) % 99999}",
            )


def render_pronunciation_section(classifier) -> None:
    import tempfile

    st.subheader("Pronunciation Lessons")
    st.caption("Listen, then record yourself. Laoshi Rara checks your tone.")

    categories = list_categories()
    default_cat = "numbers_1_10"
    category = st.selectbox(
        "Category",
        list(categories.keys()),
        index=list(categories.keys()).index(default_cat),
        format_func=lambda k: categories[k],
    )

    drills = get_drills(category)
    if not drills:
        st.warning("No drills in this category yet.")
        return

    labels = {d["id"]: d["label"] for d in drills}
    pick = st.selectbox("Choose a word", list(labels.keys()), format_func=lambda k: labels[k])
    target = next(d for d in drills if d["id"] == pick)

    with st.container(border=True):
        st.markdown(f"### Say: {target.get('pinyin', '')}")
        st.write(f"**English:** {target.get('english', '')}")
        st.write(f"**Malay:** {target.get('malay', '')}")
        if target.get("note"):
            st.caption(target.get("note", ""))

        render_speak_buttons(
            chinese=target.get("word", ""),
            english=target.get("english", ""),
            malay=target.get("malay", ""),
            key_prefix=f"pron_{target.get('id', 'word')}",
        )

        st.divider()
        st.caption("Record your voice")
        recording = st.audio_input(
            "Record",
            label_visibility="collapsed",
            key=f"rec_{target.get('id')}_{category}",
        )

        if recording is not None:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(recording.getvalue())
                wav = Path(tmp.name)

            expected = target.get("expected_tone")
            result = classifier.predict_from_file(wav)

            if not result.used_mock:
                st.caption(f"Detected: {result.label} · {result.confidence:.0%}")

            if expected and result.tone == expected:
                st.success(
                    f"Nice! {target.get('pinyin', '')} should be Tone {expected} — good job."
                )
            elif expected:
                st.error(
                    f"Try again. {target.get('pinyin', '')} should be Tone {expected}, "
                    f"but we heard Tone {result.tone}."
                )
            elif not result.used_mock:
                st.info(f"You said: {result.label}. Keep practising!")


def render_flashcards_section() -> None:
    from chatbot.flashcards import textbook_source

    st.subheader("Flashcards & Notes")
    st.caption(textbook_source())

    decks = all_decks()
    deck_id = st.selectbox(
        "Deck",
        list(decks.keys()),
        format_func=lambda d: decks[d],
    )
    cards = get_deck(deck_id)
    if not cards:
        st.info("No cards yet.")
        return

    if "card_index" not in st.session_state:
        st.session_state.card_index = 0
    if "card_flipped" not in st.session_state:
        st.session_state.card_flipped = False

    idx = st.session_state.card_index % len(cards)
    card: Flashcard = cards[idx]
    notes = load_user_notes()

    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("◀ Prev"):
        st.session_state.card_index = (idx - 1) % len(cards)
        st.session_state.card_flipped = False
        st.rerun()
    c2.markdown(f"**{idx + 1} / {len(cards)}**")
    if c3.button("Next ▶"):
        st.session_state.card_index = (idx + 1) % len(cards)
        st.session_state.card_flipped = False
        st.rerun()

    if st.button("Flip card"):
        st.session_state.card_flipped = not st.session_state.card_flipped
        st.rerun()

    with st.container(border=True):
        if st.session_state.card_flipped:
            st.markdown(f"**{card.pinyin}**")
            st.write(f"English: {card.english}")
            st.write(f"Malay: {card.malay}")
            st.caption(card.note)
        else:
            st.markdown(f"**{card.english}**")
            st.caption(f"{card.pinyin} · {card.malay}")

        render_speak_buttons(
            chinese=card.chinese,
            english=card.english,
            malay=card.malay,
            key_prefix=f"fc_{card.id}",
        )

    note = st.text_area("Your notes", value=notes.get(card.id, ""), height=80)
    if st.button("Save note"):
        notes[card.id] = note
        save_user_notes(notes)
        st.success("Saved.")
