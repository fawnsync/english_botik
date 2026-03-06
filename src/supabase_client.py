from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from supabase import Client, create_client


@dataclass
class WordRecord:
    id: int
    user_id: int
    source_word: str
    source_lang: str
    translated_word: str
    note: str | None


class SupabaseService:
    def __init__(self, url: str, key: str) -> None:
        self.client: Client = create_client(url, key)

    def ensure_user(self, user_id: int, username: str | None, first_name: str | None) -> None:
        payload: dict[str, Any] = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
        }
        self.client.table("users").upsert(payload, on_conflict="user_id").execute()

    def save_word(
        self,
        user_id: int,
        source_word: str,
        source_lang: str,
        translated_word: str,
        note: str | None,
    ) -> WordRecord:
        payload: dict[str, Any] = {
            "user_id": user_id,
            "source_word": source_word,
            "source_lang": source_lang,
            "translated_word": translated_word,
            "note": note,
        }
        response = self.client.table("words").insert(payload).execute()
        row = response.data[0]
        return WordRecord(**row)

    def get_recent_words(self, user_id: int, limit: int = 15) -> list[WordRecord]:
        response = (
            self.client.table("words")
            .select("id,user_id,source_word,source_lang,translated_word,note")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return [WordRecord(**row) for row in response.data]

    def get_all_user_ids(self) -> list[int]:
        response = self.client.table("users").select("user_id").execute()
        return [int(row["user_id"]) for row in response.data]
