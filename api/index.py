from __future__ import annotations

import os

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from src.config import get_settings
from src.dialogue import DialogueService
from src.supabase_client import SupabaseService
from src.telegram_api import TelegramAPI
from src.translator import TranslatorService
from src.webhook_logic import Services, process_update, run_daily_checkin


app = FastAPI()


def _build_services() -> Services:
    settings = get_settings()
    return Services(
        telegram=TelegramAPI(settings.telegram_bot_token),
        translator=TranslatorService(
            settings.openai_api_key,
            settings.openai_model,
            settings.openai_base_url,
            settings.llm_headers(),
        ),
        dialogue=DialogueService(
            settings.openai_api_key,
            settings.openai_model,
            settings.openai_base_url,
            settings.llm_headers(),
        ),
        supabase=SupabaseService(settings.supabase_url, settings.supabase_key),
        webapp_url=settings.webapp_url,
    )


@app.get("/")
@app.get("/api")
def health() -> dict:
    return {"ok": True, "service": "english-botik-api"}


@app.post("/telegram_webhook")
@app.post("/api/telegram_webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> JSONResponse:
    secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()
    if secret and x_telegram_bot_api_secret_token != secret:
        raise HTTPException(status_code=401, detail="Invalid telegram secret")

    update = await request.json()
    process_update(update, _build_services())
    return JSONResponse({"ok": True})


@app.get("/cron_daily")
@app.get("/api/cron_daily")
def cron_daily(authorization: str | None = Header(default=None)) -> JSONResponse:
    cron_secret = os.getenv("CRON_SECRET", "").strip()
    if cron_secret:
        expected = f"Bearer {cron_secret}"
        if authorization != expected:
            raise HTTPException(status_code=401, detail="Invalid cron secret")

    result = run_daily_checkin(_build_services())
    return JSONResponse({"ok": True, **result})


@app.get("/set_webhook")
@app.get("/api/set_webhook")
def set_webhook(setup_secret: str) -> JSONResponse:
    expected_setup_secret = os.getenv("SETUP_SECRET", "").strip()
    if expected_setup_secret and setup_secret != expected_setup_secret:
        raise HTTPException(status_code=401, detail="Invalid setup secret")

    settings = get_settings()
    base_url = os.getenv("PUBLIC_BASE_URL", "").strip()
    if not base_url:
        raise HTTPException(status_code=400, detail="PUBLIC_BASE_URL is required")

    webhook_url = f"{base_url.rstrip('/')}/api/telegram_webhook"
    api = TelegramAPI(settings.telegram_bot_token)
    response = api.set_webhook(
        webhook_url=webhook_url,
        secret_token=os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip() or None,
    )

    return JSONResponse({"ok": True, "webhook_url": webhook_url, "telegram": response})
