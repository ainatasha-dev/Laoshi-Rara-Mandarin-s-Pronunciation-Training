"""Laoshi Rara — Mandarin tutor app."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.components import (
    render_ai_chat_message,
    render_flashcards_section,
    render_pronunciation_section,
)
from audio.tone_classifier import ToneClassifier
from chatbot.ai_chat import api_key_configured, generate_laoshi_reply
from chatbot.laoshi_persona import TOPIC_FOCUS

st.set_page_config(
    page_title="Laoshi Rara",
    page_icon="👩‍🏫",
    layout="wide",
)

st.title("Laoshi Rara")
st.caption("UITM Third Language · Mandarin Level 1")

if "classifier" not in st.session_state:
    st.session_state.classifier = ToneClassifier(
        checkpoint_path=PROJECT_ROOT / "models" / "tone_classifier.pt"
    )
if "ai_history" not in st.session_state:
    st.session_state.ai_history = []
if "chat_points" not in st.session_state:
    st.session_state.chat_points = 0
if "topic_focus" not in st.session_state:
    st.session_state.topic_focus = "General"

classifier = st.session_state.classifier

with st.sidebar:
    page = st.radio(
        "Menu",
        ["Chat Laoshi", "Pronunciation Lessons", "Flashcard"],
        label_visibility="collapsed",
    )

    if page == "Chat Laoshi":
        st.divider()
        st.text_input("Your name", key="student_name", placeholder="Student")
        st.session_state.topic_focus = st.selectbox(
            "Topic focus",
            list(TOPIC_FOCUS.keys()),
        )
        st.metric("Points", st.session_state.chat_points)
        if st.button("Clear chat", use_container_width=True):
            st.session_state.ai_history = []
            st.rerun()

        if not api_key_configured():
            st.warning("Add OPENAI_API_KEY to **app.env** to enable chat.")

if page == "Flashcard":
    render_flashcards_section()
    st.stop()

if page == "Pronunciation Lessons":
    render_pronunciation_section(classifier)
    st.stop()

# --- Chat Laoshi (OpenAI, Cikgu Bot style) ---
st.subheader("Chat with Laoshi Rara")

if not api_key_configured():
    st.info(
        "Copy `app.env.example` to `app.env` and add your OpenAI API key.\n\n"
        f"File location: `{PROJECT_ROOT / 'app.env'}`"
    )

with st.container(height=450, border=True):
    history = st.session_state.ai_history
    if not history:
        st.markdown(
            "**Laoshi Rara:** Ni hao! 👋 I'm your Mandarin teacher for **UITM Level 1**. "
            "Ask me about greetings, tones, pinyin, numbers, or anything from your syllabus. "
            "I'll explain in **English** and **Malay** with **pinyin** — no Chinese characters required!"
        )
    else:
        last_ai = None
        for i, msg in enumerate(history):
            if msg.get("role") == "assistant":
                last_ai = i
        for i, msg in enumerate(history):
            render_ai_chat_message(msg, show_listen=(i == last_ai))

prompt = st.chat_input("Ask Laoshi Rara anything (English or Malay)...")
if prompt:
    reply, error = generate_laoshi_reply(
        prompt,
        st.session_state.ai_history,
        topic_key=st.session_state.topic_focus,
    )
    st.session_state.ai_history.append({"role": "user", "content": prompt})
    if error:
        st.session_state.ai_history.append({"role": "assistant", "content": error})
    else:
        st.session_state.ai_history.append({"role": "assistant", "content": reply})
        st.session_state.chat_points += 10
    st.rerun()

st.caption("Tip: use **Pronunciation Lessons** to record tones · **Flashcard** to revise vocabulary")
