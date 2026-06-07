"""Tests for the rule-based dialogue engine."""

from chatbot.dialogue_engine import DialogueEngine


def test_lesson_start_adds_bot_message():
    engine = DialogueEngine()
    messages = engine.start_lesson("lesson_1_greetings")
    assert len(messages) == 1
    assert messages[0].role == "assistant"
    assert "Hello" in messages[0].content


def test_correct_text_response_advances_step():
    engine = DialogueEngine()
    engine.start_lesson("lesson_1_greetings")
    replies = engine.submit_text("wo jiao Ana")
    assert any("meet you" in msg.meta.get("english", msg.content) for msg in replies)


def test_incorrect_text_response_gives_hint():
    engine = DialogueEngine()
    engine.start_lesson("lesson_1_greetings")
    replies = engine.submit_text("hello there")
    assert any("Hint" in msg.meta.get("english", msg.content) for msg in replies)
