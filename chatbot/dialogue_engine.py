"""Rule-based dialogue engine for Mandarin lesson practice."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from chatbot.lessons import LESSONS, TONE_LABELS


@dataclass
class ChatMessage:
    role: str
    content: str
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class DialogueState:
    lesson_id: str
    step_index: int = 0
    completed: bool = False
    history: list[ChatMessage] = field(default_factory=list)


class DialogueEngine:
    """Scripted lesson chatbot — no open-ended LLM responses."""

    def __init__(self) -> None:
        self.state: DialogueState | None = None

    @staticmethod
    def list_lessons() -> dict[str, dict[str, str]]:
        return {
            lesson_id: {
                "title": lesson["title"],
                "description": lesson["description"],
            }
            for lesson_id, lesson in LESSONS.items()
        }

    def start_lesson(self, lesson_id: str) -> list[ChatMessage]:
        if lesson_id not in LESSONS:
            raise ValueError(f"Unknown lesson: {lesson_id}")

        self.state = DialogueState(lesson_id=lesson_id)
        return self._emit_current_bot_message()

    def submit_text(self, user_text: str) -> list[ChatMessage]:
        if self.state is None or self.state.completed:
            return []

        step = self._current_step()
        normalized = user_text.strip().lower()

        if self._matches_expected(normalized, step["expected_keywords"]):
            ok_en, ok_ms = self._advance_message(step)
            feedback = ChatMessage(
                role="assistant",
                content=ok_en,
                meta={
                    "type": "feedback",
                    "correct": True,
                    "english": ok_en,
                    "malay": ok_ms,
                },
            )
            self.state.history.append(
                ChatMessage(role="user", content=user_text, meta={"type": "text"})
            )
            self.state.history.append(feedback)
            self.state.step_index += 1

            if self.state.step_index >= len(self._lesson_steps()):
                self.state.completed = True
                self.state.history.append(
                    ChatMessage(
                        role="assistant",
                        content="Lesson complete!",
                        meta={
                            "type": "lesson_complete",
                            "english": "Congratulations! You finished this lesson. Choose another lesson to continue.",
                            "malay": "Tahniah! Awak habiskan pelajaran ini. Pilih pelajaran seterusnya.",
                        },
                    )
                )
                return self.state.history[-3:]

            return self._emit_current_bot_message(prefix_messages=[feedback])

        self.state.history.append(
            ChatMessage(role="user", content=user_text, meta={"type": "text"})
        )
        hint_en = step.get("hint_en", "Try again.")
        hint_message = ChatMessage(
            role="assistant",
            content=hint_en,
            meta={
                "type": "feedback",
                "correct": False,
                "english": f"Hmm, try again. Hint: {hint_en}",
                "malay": step.get("hint_ms", f"Cuba lagi. Petunjuk: {hint_en}"),
            },
        )
        self.state.history.append(hint_message)
        return [hint_message]

    def current_speak_target(self) -> dict[str, Any] | None:
        if self.state is None or self.state.completed:
            return None
        return self._current_step().get("speak_target")

    def tone_feedback(self, predicted_tone: int) -> ChatMessage:
        target = self.current_speak_target()
        if target is None:
            return ChatMessage(
                role="assistant",
                content="No speaking step right now.",
                meta={"type": "tone_feedback", "english": "No speaking step right now."},
            )

        expected = target["expected_tone"]
        predicted_label = TONE_LABELS.get(predicted_tone, f"Tone {predicted_tone}")
        expected_label = TONE_LABELS.get(expected, f"Tone {expected}")
        pinyin = target.get("pinyin", "")

        if predicted_tone == expected:
            english = (
                f"Nice pronunciation! Target: {pinyin}. "
                f"Detected {predicted_label}."
            )
            malay = f"Sebutan bagus! Sasaran: {pinyin}. Dikesan {predicted_label}."
            correct = True
        else:
            english = (
                f"Watch the tone: {pinyin} should be {expected_label}, "
                f"but we heard {predicted_label}. Try again."
            )
            malay = (
                f"Perhatikan nada: {pinyin} patut {expected_label}, "
                f"tetapi kami dengar {predicted_label}. Cuba lagi."
            )
            correct = False

        message = ChatMessage(
            role="assistant",
            content=english,
            meta={
                "type": "tone_feedback",
                "correct": correct,
                "english": english,
                "malay": malay,
                "expected_tone": expected,
                "predicted_tone": predicted_tone,
                "pinyin": pinyin,
            },
        )
        self.state.history.append(message)
        return message

    def get_history(self) -> list[ChatMessage]:
        return self.state.history if self.state else []

    def _lesson_steps(self) -> list[dict[str, Any]]:
        assert self.state is not None
        return LESSONS[self.state.lesson_id]["steps"]

    def _current_step(self) -> dict[str, Any]:
        return self._lesson_steps()[self.state.step_index]

    def _emit_current_bot_message(
        self, prefix_messages: list[ChatMessage] | None = None
    ) -> list[ChatMessage]:
        step = self._current_step()
        bot_message = ChatMessage(
            role="assistant",
            content=step.get("bot_english", step.get("bot_pinyin", "")),
            meta={
                "type": "prompt",
                "chinese": step["bot"],
                "pinyin": step.get("bot_pinyin", ""),
                "english": step.get("bot_english", ""),
                "malay": step.get("bot_malay", ""),
                "speak_target": step.get("speak_target"),
            },
        )
        self.state.history.append(bot_message)
        emitted = prefix_messages[:] if prefix_messages else []
        emitted.append(bot_message)
        return emitted

    @staticmethod
    def _advance_message(step: dict[str, Any]) -> tuple[str, str]:
        """Friendly continuation lines — not quiz-style 'correct answer'."""
        if step.get("advance_en"):
            return step["advance_en"], step.get("advance_ms", step["advance_en"])

        step_id = step.get("id", "")
        if step_id in {"num_intro", "tone_intro"}:
            return "Okay, let's begin!", "Baik, jom mula!"
        if step_id == "greet_1":
            return "Nice to meet you! Let's continue.", "Gembira berkenalan! Mari teruskan."
        speak = step.get("speak_target")
        if speak:
            pinyin = speak.get("pinyin", "")
            return (
                f"Good! Now say it out loud: {pinyin}.",
                f"Bagus! Sekarang sebut: {pinyin}.",
            )
        return "Nice — let's keep going!", "Baik — mari teruskan!"

    @staticmethod
    def _matches_expected(normalized_input: str, keywords: list[str]) -> bool:
        return any(keyword.lower() in normalized_input for keyword in keywords)
