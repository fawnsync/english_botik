from __future__ import annotations

import os

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from src.config import get_settings
from src.dialogue import DialogueService
from src.supabase_client import SupabaseService
from src.telegram_api import TelegramAPI
from src.translator import TranslatorService
from src.webhook_logic import Services, process_update


app = FastAPI()


def _build_services() -> Services:
    settings = get_settings()
    return Services(
        telegram=TelegramAPI(settings.telegram_bot_token),
        translator=TranslatorService(settings.openai_api_key, settings.openai_model),
        dialogue=DialogueService(settings.openai_api_key, settings.openai_model),
        supabase=SupabaseService(settings.supabase_url, settings.supabase_key),
        webapp_url=settings.webapp_url,
    )


@app.get("/")
def health() -> dict:
    return {"ok": True}


@app.post("/")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> JSONResponse:
    secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()
    if secret and x_telegram_bot_api_secret_token != secret:
        raise HTTPException(status_code=401, detail="Invalid telegram secret")

    update = await request.json()
    services = _build_services()
    process_update(update, services)
    return JSONResponse({"ok": True})
