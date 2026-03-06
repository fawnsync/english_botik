from __future__ import annotations

from dataclasses import dataclass

from openai import OpenAI

from src.supabase_client import WordRecord


@dataclass
class DialogueReply:
    corrected_text: str | None
    correction_reason: str | None
    assistant_reply: str


class DialogueService:
    def __init__(self, api_key: str, model: str) -> None:
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def _words_context(self, words: list[WordRecord]) -> str:
        if not words:
            return "No saved words yet."
        lines = [
            f"- {w.source_word} -> {w.translated_word}"
            for w in words[:12]
        ]
        return "\n".join(lines)

    def build_daily_prompt(self, words: list[WordRecord]) -> str:
        words_ctx = self._words_context(words)
        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "Write one friendly English message asking user about their day. "
                        "Try to naturally include 1-2 words from the provided list if possible. "
                        "Return one short message only."
                    ),
                },
                {"role": "user", "content": f"Words:\n{words_ctx}"},
            ],
            temperature=0.6,
        )
        return response.output_text.strip()

    def respond_to_user(self, user_text: str, words: list[WordRecord]) -> DialogueReply:
        words_ctx = self._words_context(words)
        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are an English tutor in Telegram chat. "
                        "Answer in English. "
                        "If user has mistakes, first provide corrected sentence and very short rule-based reason. "
                        "Then continue supportive dialogue with one question. "
                        "Try to naturally reuse words from provided list. "
                        "Response format strictly:\n"
                        "CORRECTED: <text or NONE>\n"
                        "REASON: <reason or NONE>\n"
                        "REPLY: <assistant reply>"
                    ),
                },
                {
                    "role": "user",
                    "content": f"Saved words:\n{words_ctx}\n\nUser message:\n{user_text}",
                },
            ],
            temperature=0.5,
        )

        raw = response.output_text.strip().splitlines()
        corrected = None
        reason = None
        reply = "Could you tell me a bit more about your day?"

        for line in raw:
            if line.startswith("CORRECTED:"):
                value = line.replace("CORRECTED:", "", 1).strip()
                corrected = None if value.upper() == "NONE" else value
            elif line.startswith("REASON:"):
                value = line.replace("REASON:", "", 1).strip()
                reason = None if value.upper() == "NONE" else value
            elif line.startswith("REPLY:"):
                reply = line.replace("REPLY:", "", 1).strip()

        return DialogueReply(
            corrected_text=corrected,
            correction_reason=reason,
            assistant_reply=reply,
        )
