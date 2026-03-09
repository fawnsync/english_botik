from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from src.config import get_settings
from src.telegram_api import TelegramAPI


app = FastAPI()


@app.get("/")
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
