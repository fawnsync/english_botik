from __future__ import annotations

import os

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse

from src.config import get_settings
from src.dialogue import DialogueService
from src.supabase_client import SupabaseService
from src.telegram_api import TelegramAPI
from src.translator import TranslatorService
from src.webhook_logic import Services, run_daily_checkin


app = FastAPI()


def _build_services() -> Services:
    settings = get_settings()
    return Services(
        telegram=TelegramAPI(settings.telegram_bot_token),
        translator=TranslatorService(settings.openai_api_key, settings.openai_model, settings.openai_base_url, settings.llm_headers()),
        dialogue=DialogueService(settings.openai_api_key, settings.openai_model, settings.openai_base_url, settings.llm_headers()),
        supabase=SupabaseService(settings.supabase_url, settings.supabase_key),
        webapp_url=settings.webapp_url,
    )


@app.get("/")
def cron_daily(authorization: str | None = Header(default=None)) -> JSONResponse:
    cron_secret = os.getenv("CRON_SECRET", "").strip()
    if cron_secret:
        expected = f"Bearer {cron_secret}"
        if authorization != expected:
            raise HTTPException(status_code=401, detail="Invalid cron secret")

    result = run_daily_checkin(_build_services())
    return JSONResponse({"ok": True, **result})
