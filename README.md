# Telegram English Tutor Mini App + Bot

Проект: красивый Telegram Mini App + бот-помощник для изучения английского.

Функции:
- Переводчик RU <-> EN
- Пояснение исключений/особенностей (например `man -> men`)
- Сохранение слов в Supabase
- Ежедневный check-in вопрос на английском
- Диалог с исправлением ошибок и объяснением правил
- Бот старается использовать слова из вашей базы в общении

## Структура

- `src/bot.py` - Telegram бот (aiogram)
- `src/translator.py` - перевод и объяснения через OpenAI
- `src/dialogue.py` - режим общения и исправления
- `src/supabase_client.py` - запись/чтение слов из Supabase
- `src/scheduler.py` - ежедневные сообщения
- `sql/schema.sql` - SQL схема Supabase
- `web/` - фронтенд Telegram Mini App

## 1) Установка

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 2) Настройка переменных

Скопируйте `.env.example` в `.env` и заполните:

- `TELEGRAM_BOT_TOKEN`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `DAILY_CHECKIN_HOUR`
- `TIMEZONE`
- `WEBAPP_URL` (URL на ваш `web/index.html` по HTTPS)

## 3) Настройка Supabase

Выполните SQL из `sql/schema.sql` в SQL Editor вашего Supabase.

## 4) Публикация Mini App фронтенда

Папку `web/` нужно выложить на HTTPS-хостинг (например Netlify/Vercel/GitHub Pages через кастомный HTTPS URL).

Требуется, чтобы `WEBAPP_URL` указывал на `index.html`.

## 5) Запуск бота

```bash
python -m src.bot
```

## Использование

- `/start` - регистрация и кнопка открытия Mini App
- `/app` - открыть Mini App кнопкой
- `/translate word` - перевод + кнопка сохранения
- `/chat I goed to school` - диалог с исправлениями
- Любое обычное сообщение тоже работает как тренировка

## Важно

- Бот должен работать постоянно для ежедневных сообщений.
- История чатов не сохраняется, сохраняются слова.
