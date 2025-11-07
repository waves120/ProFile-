
# Favorites Pro — Telegram Bot (Local)

Локальный Telegram-бот для сохранения ссылок и файлов по «доскам». Хранение — SQLite, файлы — через `file_id` Telegram.

## Возможности
- Принимает ссылки (в тексте) и файлы (фото/док/видео ≤ 50 MB).
- Просит подтвердить/изменить название — inline-кнопки.
- Дает выбрать доску или создать новую — inline-кнопки.
- Команды:
  - `/boards` — список досок;
  - `/show <доска>` — элементы в доске;
  - `/view <название>` — высылает ссылку/файл по названию;
  - `/move <название> <доска>` — перенос элемента;
  - `/remove <название>` — удаление.
- Теги: слова вида `#python` в названии/подписи сохраняются в поле `tags`.
- БД: SQLite (async, SQLAlchemy 2.x); таблицы создаются автоматически.

## Запуск локально (Windows 11/ Linux/ macOS)
1. Создай бота у @BotFather и получи токен.
2. Скопируй `.env.example` в `.env` и вставь токен:
   ```env
   BOT_TOKEN=123456:ABC...
   DB_URL=sqlite+aiosqlite:///./data/bot.db
   ```
3. Установи Python 3.11+ и зависимости:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   # source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. Запусти бота:
   ```bash
   python -m app.bot
   ```

## Docker (опционально)
```bash
docker build -t favorites-pro-bot .
docker run --env-file .env -v $(pwd)/data:/app/data favorites-pro-bot
# или
docker compose up -d
```

## Структура
```
app/
  bot.py        – точка входа и маршрутизация
  config.py     – загрузка .env
  db.py         – модели и инициализация БД
  fsm.py        – состояния мастера добавления
  keyboards.py  – inline-кнопки
  utils.py      – парсер ссылок/тегов
```

## Примечания
- Бот хранит только `file_id` — сами файлы остаются у Telegram.
- Уникальность элемента по (`user_id`, `title`) — удобно обращаться по названию.
