# Telegram English Tutor Mini App (Vercel)

Проект полностью адаптирован под Vercel:
- Mini App фронтенд: `web/`
- Telegram webhook: `/api/telegram_webhook`
- Ежедневный check-in через Vercel Cron: `/api/cron_daily`
- Endpoint для установки webhook: `/api/set_webhook`

## Что уже умеет
- Перевод RU/EN + пояснение исключений
- Сохранение слова в Supabase
- Диалог с исправлением ошибок и коротким объяснением правила
- Ежедневное сообщение на английском с использованием слов из вашей БД

## Файлы
- `api/telegram_webhook.py` - обработка апдейтов Telegram
- `api/cron_daily.py` - ежедневные сообщения
- `api/set_webhook.py` - установка webhook в Telegram
- `src/webhook_logic.py` - общая логика бота
- `sql/schema.sql` - таблицы Supabase
- `web/` - интерфейс Mini App
- `vercel.json` - расписание Cron

## Переменные окружения в Vercel
Добавьте в Vercel Project Settings -> Environment Variables:

- `TELEGRAM_BOT_TOKEN`
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (например `gpt-4.1-mini`)
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `WEBAPP_URL` (например `https://your-project.vercel.app/web/index.html`)
- `PUBLIC_BASE_URL` (например `https://your-project.vercel.app`)
- `TELEGRAM_WEBHOOK_SECRET` (любая случайная строка)
- `SETUP_SECRET` (любая случайная строка)
- `CRON_SECRET` (любая случайная строка)

## Настройка BotFather
1. `/setdomain` -> укажите `https://your-project.vercel.app`
2. `/setmenubutton` (опционально) -> Mini App URL `https://your-project.vercel.app/web/index.html`

## Установка webhook
После деплоя откройте:

`https://your-project.vercel.app/api/set_webhook?setup_secret=YOUR_SETUP_SECRET`

Это привяжет Telegram к:

`https://your-project.vercel.app/api/telegram_webhook`

## Supabase
Выполните SQL из `sql/schema.sql` (если еще не выполнено).

## Проверка
1. Откройте бота и отправьте `/start`
2. Нажмите `Open Mini App`
3. Проверьте перевод и сохранение слова
4. Проверьте чат-команду `/chat ...`

## Cron
`vercel.json` уже содержит ежедневный запуск `/api/cron_daily` в `17:00 UTC` (это `20:00` по Москве).
