from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

from src.config import get_settings
from src.dialogue import DialogueService
from src.scheduler import DailyCheckinScheduler
from src.supabase_client import SupabaseService
from src.translator import TranslationResult, TranslatorService


logging.basicConfig(level=logging.INFO)


@dataclass
class UserState:
    pending_translation: TranslationResult | None = None


user_state: dict[int, UserState] = {}


def get_or_create_state(user_id: int) -> UserState:
    if user_id not in user_state:
        user_state[user_id] = UserState()
    return user_state[user_id]


def build_start_keyboard(webapp_url: str) -> InlineKeyboardMarkup | None:
    if not webapp_url:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Open Mini App",
                    web_app=WebAppInfo(url=webapp_url),
                )
            ]
        ]
    )


async def main() -> None:
    settings = get_settings()

    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()

    translator = TranslatorService(settings.openai_api_key, settings.openai_model, settings.openai_base_url, settings.llm_headers())
    dialogue = DialogueService(settings.openai_api_key, settings.openai_model, settings.openai_base_url, settings.llm_headers())
    supabase = SupabaseService(settings.supabase_url, settings.supabase_key)

    scheduler = DailyCheckinScheduler(
        bot=bot,
        supabase=supabase,
        dialogue=dialogue,
        hour=settings.daily_checkin_hour,
        timezone=settings.timezone,
    )
    scheduler.start()

    @dp.message(Command("start"))
    async def start_handler(message: Message) -> None:
        if not message.from_user:
            return
        supabase.ensure_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
        await message.answer(
            "Hi! I am your English learning assistant.\n\n"
            "Commands:\n"
            "/translate <word> - translate and explain grammar exceptions\n"
            "/chat <message> - practice dialogue with corrections\n"
            "You can also send plain text, and I will reply as your tutor.",
            reply_markup=build_start_keyboard(settings.webapp_url),
        )

    @dp.message(Command("app"))
    async def app_handler(message: Message) -> None:
        keyboard = build_start_keyboard(settings.webapp_url)
        if not keyboard:
            await message.answer("WEBAPP_URL is not set in .env")
            return
        await message.answer("Open the mini app:", reply_markup=keyboard)

    @dp.message(Command("translate"))
    async def translate_handler(message: Message, command: CommandObject) -> None:
        if not message.from_user:
            return
        if not command.args:
            await message.answer("Usage: /translate <word>")
            return

        await run_translation(
            message=message,
            text=command.args,
            translator=translator,
            supabase=supabase,
            save=False,
        )

    @dp.callback_query(F.data == "save_last_word")
    async def save_last_word_handler(callback: CallbackQuery) -> None:
        if not callback.from_user:
            return

        state = get_or_create_state(callback.from_user.id)
        if not state.pending_translation:
            await callback.answer("No word to save", show_alert=True)
            return

        result = state.pending_translation
        supabase.save_word(
            user_id=callback.from_user.id,
            source_word=result.source_word,
            source_lang=result.source_lang,
            translated_word=result.translated_word,
            note=result.grammar_exception or result.explanation,
        )

        await callback.answer("Saved")
        if callback.message:
            await callback.message.answer(
                f"Saved: {result.source_word} -> {result.translated_word}"
            )

    @dp.message(F.web_app_data)
    async def webapp_data_handler(message: Message) -> None:
        if not message.from_user or not message.web_app_data:
            return

        try:
            payload = json.loads(message.web_app_data.data)
            action = payload.get("action")
        except Exception:
            await message.answer("Mini app payload is invalid")
            return

        if action == "translate":
            text = str(payload.get("text", "")).strip()
            save = bool(payload.get("save", False))
            if not text:
                await message.answer("Please enter a word")
                return
            await run_translation(
                message=message,
                text=text,
                translator=translator,
                supabase=supabase,
                save=save,
            )
            return

        if action == "chat":
            text = str(payload.get("text", "")).strip()
            if not text:
                await message.answer("Please enter your message")
                return
            await process_dialogue(message, text, dialogue, supabase)
            return

        await message.answer("Unknown mini app action")

    @dp.message(Command("chat"))
    async def chat_handler(message: Message, command: CommandObject) -> None:
        if not message.from_user:
            return
        if not command.args:
            await message.answer("Usage: /chat <your message>")
            return
        await process_dialogue(message, command.args, dialogue, supabase)

    @dp.message(F.text)
    async def plain_text_handler(message: Message) -> None:
        if not message.from_user or not message.text:
            return

        text = message.text.strip()
        if text.startswith("/"):
            return

        await process_dialogue(message, text, dialogue, supabase)

    await dp.start_polling(bot)


async def run_translation(
    message: Message,
    text: str,
    translator: TranslatorService,
    supabase: SupabaseService,
    save: bool,
) -> None:
    if not message.from_user:
        return

    try:
        result = translator.translate_word(text)
    except Exception as err:
        await message.answer(f"Translation failed: {err}")
        return

    exception_part = (
        f"\nException: {result.grammar_exception}"
        if result.grammar_exception
        else "\nException: none"
    )

    if save:
        supabase.save_word(
            user_id=message.from_user.id,
            source_word=result.source_word,
            source_lang=result.source_lang,
            translated_word=result.translated_word,
            note=result.grammar_exception or result.explanation,
        )
        await message.answer(
            f"Source: {result.source_word} ({result.source_lang})\n"
            f"Translation: {result.translated_word}\n"
            f"Note: {result.explanation}"
            f"{exception_part}\n"
            "Saved to Supabase"
        )
        return

    state = get_or_create_state(message.from_user.id)
    state.pending_translation = result

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Save to Supabase", callback_data="save_last_word")]
        ]
    )

    await message.answer(
        f"Source: {result.source_word} ({result.source_lang})\n"
        f"Translation: {result.translated_word}\n"
        f"Note: {result.explanation}"
        f"{exception_part}",
        reply_markup=keyboard,
    )


async def process_dialogue(
    message: Message,
    user_text: str,
    dialogue: DialogueService,
    supabase: SupabaseService,
) -> None:
    if not message.from_user:
        return

    try:
        words = supabase.get_recent_words(message.from_user.id, limit=15)
        reply = dialogue.respond_to_user(user_text, words)
    except Exception as err:
        await message.answer(f"Chat failed: {err}")
        return

    parts: list[str] = []
    if reply.corrected_text:
        parts.append(f"Correction: {reply.corrected_text}")
    if reply.correction_reason:
        parts.append(f"Why: {reply.correction_reason}")
    parts.append(reply.assistant_reply)

    await message.answer("\n".join(parts))


if __name__ == "__main__":
    asyncio.run(main())
