from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot

from src.dialogue import DialogueService
from src.supabase_client import SupabaseService


class DailyCheckinScheduler:
    def __init__(
        self,
        bot: Bot,
        supabase: SupabaseService,
        dialogue: DialogueService,
        hour: int,
        timezone: str,
    ) -> None:
        self.bot = bot
        self.supabase = supabase
        self.dialogue = dialogue
        self.scheduler = AsyncIOScheduler(timezone=timezone)
        self.hour = hour

    def start(self) -> None:
        trigger = CronTrigger(hour=self.hour, minute=0)
        self.scheduler.add_job(self._run_daily, trigger=trigger, id="daily_checkin", replace_existing=True)
        self.scheduler.start()

    async def _run_daily(self) -> None:
        user_ids = self.supabase.get_all_user_ids()
        for user_id in user_ids:
            try:
                words = self.supabase.get_recent_words(user_id=user_id, limit=15)
                message = self.dialogue.build_daily_prompt(words)
                await self.bot.send_message(chat_id=user_id, text=message)
            except Exception:
                # Skip individual user errors to keep batch delivery running.
                continue
