from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    openai_api_key: str
    openai_model: str
    openai_base_url: str
    openrouter_http_referer: str
    openrouter_app_title: str
    supabase_url: str
    supabase_key: str
    daily_checkin_hour: int
    timezone: str
    webapp_url: str

    def llm_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.openrouter_http_referer:
            headers["HTTP-Referer"] = self.openrouter_http_referer
        if self.openrouter_app_title:
            headers["X-Title"] = self.openrouter_app_title
        return headers


def _resolve_llm_api_key() -> str:
    return os.getenv("OPENAI_API_KEY", "") or os.getenv("OPENROUTER_API_KEY", "")


def _resolve_llm_model() -> str:
    return os.getenv("OPENAI_MODEL", "") or os.getenv("OPENROUTER_MODEL", "gpt-4.1-mini")


def _resolve_llm_base_url(api_key: str) -> str:
    explicit = os.getenv("OPENAI_BASE_URL", "").strip()
    if explicit:
        return explicit
    if api_key.startswith("sk-or-"):
        return "https://openrouter.ai/api/v1"
    return ""


def get_settings() -> Settings:
    llm_api_key = _resolve_llm_api_key()

    settings = Settings(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        openai_api_key=llm_api_key,
        openai_model=_resolve_llm_model(),
        openai_base_url=_resolve_llm_base_url(llm_api_key),
        openrouter_http_referer=os.getenv("OPENROUTER_HTTP_REFERER", "").strip(),
        openrouter_app_title=os.getenv("OPENROUTER_APP_TITLE", "").strip(),
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_key=os.getenv("SUPABASE_KEY", ""),
        daily_checkin_hour=int(os.getenv("DAILY_CHECKIN_HOUR", "20")),
        timezone=os.getenv("TIMEZONE", "Europe/Moscow"),
        webapp_url=os.getenv("WEBAPP_URL", ""),
    )

    missing = [
        key
        for key, value in {
            "TELEGRAM_BOT_TOKEN": settings.telegram_bot_token,
            "OPENAI_API_KEY or OPENROUTER_API_KEY": settings.openai_api_key,
            "SUPABASE_URL": settings.supabase_url,
            "SUPABASE_KEY": settings.supabase_key,
        }.items()
        if not value
    ]

    if missing:
        raise ValueError(f"Missing required env vars: {', '.join(missing)}")

    if not (0 <= settings.daily_checkin_hour <= 23):
        raise ValueError("DAILY_CHECKIN_HOUR must be between 0 and 23")

    return settings
