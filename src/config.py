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
    supabase_url: str
    supabase_key: str
    daily_checkin_hour: int
    timezone: str
    webapp_url: str


def get_settings() -> Settings:
    settings = Settings(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
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
            "OPENAI_API_KEY": settings.openai_api_key,
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
