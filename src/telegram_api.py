from __future__ import annotations

import httpx


class TelegramAPI:
    def __init__(self, bot_token: str) -> None:
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, chat_id: int, text: str, reply_markup: dict | None = None) -> None:
        payload: dict = {
            "chat_id": chat_id,
            "text": text,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        with httpx.Client(timeout=20) as client:
            client.post(f"{self.base_url}/sendMessage", json=payload)

    def answer_callback_query(
        self,
        callback_query_id: str,
        text: str | None = None,
        show_alert: bool = False,
    ) -> None:
        payload: dict = {"callback_query_id": callback_query_id, "show_alert": show_alert}
        if text:
            payload["text"] = text
        with httpx.Client(timeout=20) as client:
            client.post(f"{self.base_url}/answerCallbackQuery", json=payload)

    def set_webhook(self, webhook_url: str, secret_token: str | None = None) -> dict:
        payload: dict = {"url": webhook_url}
        if secret_token:
            payload["secret_token"] = secret_token
        with httpx.Client(timeout=20) as client:
            response = client.post(f"{self.base_url}/setWebhook", json=payload)
            response.raise_for_status()
            return response.json()
