from __future__ import annotations

from dataclasses import dataclass

from src.dialogue import DialogueService
from src.supabase_client import SupabaseService
from src.telegram_api import TelegramAPI
from src.translator import TranslatorService


@dataclass
class Services:
    telegram: TelegramAPI
    translator: TranslatorService
    dialogue: DialogueService
    supabase: SupabaseService
    webapp_url: str


def _start_keyboard(webapp_url: str) -> dict | None:
    if not webapp_url:
        return None
    return {
        "inline_keyboard": [[{"text": "Open Mini App", "web_app": {"url": webapp_url}}]],
    }


def _save_keyboard(source_word: str) -> dict:
    return {
        "inline_keyboard": [[{"text": "Save to Supabase", "callback_data": f"save:{source_word}"}]],
    }


def _format_translation(result) -> str:
    exception_part = f"\nException: {result.grammar_exception}" if result.grammar_exception else "\nException: none"
    return (
        f"Source: {result.source_word} ({result.source_lang})\n"
        f"Translation: {result.translated_word}\n"
        f"Note: {result.explanation}"
        f"{exception_part}"
    )


def _ensure_user(services: Services, user: dict) -> None:
    services.supabase.ensure_user(
        user_id=int(user["id"]),
        username=user.get("username"),
        first_name=user.get("first_name"),
    )


def process_update(update: dict, services: Services) -> None:
    if "message" in update:
        _handle_message(update["message"], services)
        return
    if "callback_query" in update:
        _handle_callback(update["callback_query"], services)


def _handle_message(message: dict, services: Services) -> None:
    from_user = message.get("from")
    chat = message.get("chat")
    if not from_user or not chat:
        return

    user_id = int(from_user["id"])
    chat_id = int(chat["id"])
    _ensure_user(services, from_user)

    web_data = message.get("web_app_data")
    if web_data and web_data.get("data"):
        _handle_webapp_data(chat_id, user_id, web_data["data"], services)
        return

    text = (message.get("text") or "").strip()
    if not text:
        return

    if text.startswith("/start"):
        services.telegram.send_message(
            chat_id=chat_id,
            text=(
                "Hi! I am your English learning assistant.\n\n"
                "Commands:\n"
                "/translate <word> - translate and explain grammar exceptions\n"
                "/chat <message> - practice dialogue with corrections\n"
                "You can also send plain text, and I will reply as your tutor."
            ),
            reply_markup=_start_keyboard(services.webapp_url),
        )
        return

    if text.startswith("/app"):
        keyboard = _start_keyboard(services.webapp_url)
        services.telegram.send_message(
            chat_id=chat_id,
            text="Open the mini app" if keyboard else "WEBAPP_URL is not configured",
            reply_markup=keyboard,
        )
        return

    if text.startswith("/translate"):
        word = text.replace("/translate", "", 1).strip()
        if not word:
            services.telegram.send_message(chat_id=chat_id, text="Usage: /translate <word>")
            return
        _run_translation(chat_id, user_id, word, services, save=False)
        return

    if text.startswith("/chat"):
        user_text = text.replace("/chat", "", 1).strip()
        if not user_text:
            services.telegram.send_message(chat_id=chat_id, text="Usage: /chat <your message>")
            return
        _run_dialogue(chat_id, user_id, user_text, services)
        return

    if text.startswith("/"):
        return

    _run_dialogue(chat_id, user_id, text, services)


def _handle_webapp_data(chat_id: int, user_id: int, raw_data: str, services: Services) -> None:
    import json

    try:
        payload = json.loads(raw_data)
    except Exception:
        services.telegram.send_message(chat_id=chat_id, text="Mini app payload is invalid")
        return

    action = payload.get("action")
    text = str(payload.get("text", "")).strip()

    if action == "translate":
        if not text:
            services.telegram.send_message(chat_id=chat_id, text="Please enter a word")
            return
        _run_translation(chat_id, user_id, text, services, save=bool(payload.get("save", False)))
        return

    if action == "chat":
        if not text:
            services.telegram.send_message(chat_id=chat_id, text="Please enter your message")
            return
        _run_dialogue(chat_id, user_id, text, services)
        return

    services.telegram.send_message(chat_id=chat_id, text="Unknown mini app action")


def _handle_callback(callback_query: dict, services: Services) -> None:
    callback_id = callback_query.get("id")
    from_user = callback_query.get("from")
    message = callback_query.get("message")
    data = (callback_query.get("data") or "").strip()

    if not callback_id or not from_user or not message:
        return

    chat = message.get("chat") or {}
    chat_id = int(chat.get("id", 0))
    user_id = int(from_user["id"])

    if not data.startswith("save:"):
        services.telegram.answer_callback_query(str(callback_id), text="Unknown action", show_alert=True)
        return

    source_word = data.replace("save:", "", 1).strip()
    if not source_word:
        services.telegram.answer_callback_query(str(callback_id), text="No word to save", show_alert=True)
        return

    try:
        result = services.translator.translate_word(source_word)
        services.supabase.save_word(
            user_id=user_id,
            source_word=result.source_word,
            source_lang=result.source_lang,
            translated_word=result.translated_word,
            note=result.grammar_exception or result.explanation,
        )
    except Exception:
        services.telegram.answer_callback_query(str(callback_id), text="Save failed", show_alert=True)
        return

    services.telegram.answer_callback_query(str(callback_id), text="Saved")
    if chat_id:
        services.telegram.send_message(chat_id=chat_id, text=f"Saved: {result.source_word} -> {result.translated_word}")


def _run_translation(chat_id: int, user_id: int, text: str, services: Services, save: bool) -> None:
    try:
        result = services.translator.translate_word(text)
    except Exception as err:
        services.telegram.send_message(chat_id=chat_id, text=f"Translation failed: {err}")
        return

    if save:
        try:
            services.supabase.save_word(
                user_id=user_id,
                source_word=result.source_word,
                source_lang=result.source_lang,
                translated_word=result.translated_word,
                note=result.grammar_exception or result.explanation,
            )
        except Exception as err:
            services.telegram.send_message(chat_id=chat_id, text=f"Save failed: {err}")
            return
        services.telegram.send_message(chat_id=chat_id, text=f"{_format_translation(result)}\nSaved to Supabase")
        return

    services.telegram.send_message(
        chat_id=chat_id,
        text=_format_translation(result),
        reply_markup=_save_keyboard(result.source_word),
    )


def _run_dialogue(chat_id: int, user_id: int, user_text: str, services: Services) -> None:
    try:
        words = services.supabase.get_recent_words(user_id=user_id, limit=15)
        reply = services.dialogue.respond_to_user(user_text, words)
    except Exception as err:
        services.telegram.send_message(chat_id=chat_id, text=f"Chat failed: {err}")
        return

    parts: list[str] = []
    if reply.corrected_text:
        parts.append(f"Correction: {reply.corrected_text}")
    if reply.correction_reason:
        parts.append(f"Why: {reply.correction_reason}")
    parts.append(reply.assistant_reply)

    services.telegram.send_message(chat_id=chat_id, text="\n".join(parts))


def run_daily_checkin(services: Services) -> dict:
    sent = 0
    failed = 0

    user_ids = services.supabase.get_all_user_ids()
    for user_id in user_ids:
        try:
            words = services.supabase.get_recent_words(user_id=user_id, limit=15)
            message = services.dialogue.build_daily_prompt(words)
            services.telegram.send_message(chat_id=user_id, text=message)
            sent += 1
        except Exception:
            failed += 1

    return {"sent": sent, "failed": failed, "total": len(user_ids)}
