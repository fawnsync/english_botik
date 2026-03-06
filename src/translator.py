from __future__ import annotations

import json
from dataclasses import dataclass

from openai import OpenAI


@dataclass
class TranslationResult:
    source_word: str
    source_lang: str
    translated_word: str
    explanation: str
    grammar_exception: str | None


class TranslatorService:
    def __init__(self, api_key: str, model: str) -> None:
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def translate_word(self, text: str) -> TranslationResult:
        prompt = (
            "You are an English-Russian word translator. "
            "Detect source language automatically (en or ru). "
            "Return only JSON with keys: "
            "source_word, source_lang, translated_word, explanation, grammar_exception. "
            "If no exception, grammar_exception must be null. "
            "Explanation must be concise and useful for learners."
        )

        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text.strip()},
            ],
            temperature=0.2,
        )

        raw_text = response.output_text.strip()

        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError:
            # Defensive fallback if the model returns wrappers around JSON.
            start = raw_text.find("{")
            end = raw_text.rfind("}")
            if start == -1 or end == -1:
                raise ValueError("Model response is not valid JSON")
            payload = json.loads(raw_text[start : end + 1])

        return TranslationResult(
            source_word=payload["source_word"],
            source_lang=payload["source_lang"],
            translated_word=payload["translated_word"],
            explanation=payload["explanation"],
            grammar_exception=payload.get("grammar_exception"),
        )
