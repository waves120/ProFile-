import csv
import logging
import os
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
)

# --- 1. НАСТРОЙКА И КОНСТАНТЫ ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8431149145:AAH42OdhXeGDimtSD828RtVgN3qLI2EiPmc" # <-- ЗАМЕНИТЕ НА ВАШ ТОКЕН
DB_FILE = "database.csv"
BOARDS_FILE = "boards.csv"

# Этапы для диалогов
(WAITING_CONTENT, ASK_TITLE, ASK_BOARD, CREATE_BOARD) = range(4)
ASK_NEW_NAME = range(4, 5)


# --- 2. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (РАБОТА С CSV) ---

def initialize_db():
    for filename, headers in [
        (DB_FILE, ["user_id", "item_title", "board", "item_type", "content"]),
        (BOARDS_FILE, ["user_id", "board_name"])
    ]:
        if not os.path.exists(filename):
            with open(filename, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(headers)

# --- Функции для ДОСОК ---
def get_user_boards(user_id: int) -> list:
    boards = set()
    if os.path.exists(BOARDS_FILE):
        with open(BOARDS_FILE, "r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if int(row["user_id"]) == user_id: boards.add(row["board_name"])
    with open(DB_FILE, "r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if int(row["user_id"]) == user_id: boards.add(row["board"])
    return sorted(list(boards))

def add_board(user_id: int, board_name: str):
    with open(BOARDS_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([user_id, board_name])

def rename_board(user_id: int, old_name: str, new_name: str) -> bool:
    # 1. Переименовать в основной базе
    db_rows = read_db_rows()
    renamed_in_db = False
    for row in db_rows[1:]:
        if int(row[0]) == user_id and row[2].lower() == old_name.lower():
            row[2] = new_name
            renamed_in_db = True
    if renamed_in_db:
        write_db_rows(db_rows)
    
    # 2. Переименовать в файле пустых досок
    board_rows, renamed_in_boards_db = [], False
    if os.path.exists(BOARDS_FILE):
        with open(BOARDS_FILE, "r", newline="", encoding="utf-8") as f:
            board_rows = list(csv.reader(f))
        for row in board_rows[1:]:
            if int(row[0]) == user_id and row[1].lower() == old_name.lower():
                row[1] = new_name
                renamed_in_boards_db = True
        if renamed_in_boards_db:
            with open(BOARDS_FILE, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerows(board_rows)
    return True

def delete_board(user_id: int, board_name: str) -> bool:
    # Удаляем только из файла пустых досок, т.к. нельзя удалять непустую
    if not os.path.exists(BOARDS_FILE): return False
    
    rows, removed = [], False
    with open(BOARDS_FILE, "r", newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    
    new_rows = [rows[0]]
    for row in rows[1:]:
        if int(row[0]) == user_id and row[1].lower() == board_name.lower():
            removed = True
        else:
            new_rows.append(row)
    
    if removed:
        with open(BOARDS_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(new_rows)
    return removed

# --- Функции для ФАЙЛОВ ---
def is_title_unique(user_id: int, title: str) -> bool:
    # ... (код без изменений) ...
    return True

def save_item(user_id: int, title: str, board: str, item_type: str, content: str):
    # ... (код без изменений) ...
    pass

def get_items_in_board(user_id: int, board: str) -> list:
    # ... (код без изменений) ...
    return []

def find_item_by_title(user_id: int, title: str) -> dict | None:
    # ... (код без изменений) ...
    return None

def read_db_rows():
    # ... (код без изменений) ...
    return []

def write_db_rows(rows):
    # ... (код без изменений) ...
    pass

def remove_item(user_id: int, title: str) -> bool:
    # ... (код без изменений) ...
    return True

def move_item(user_id: int, title: str, new_board: str) -> bool:
    # ... (код без изменений) ...
    return True

def rename_item(user_id: int, old_title: str, new_title: str) -> bool:
    # ... (код без изменений) ...
    return True

def get_url_title(url: str) -> str:
    # ... (код без изменений) ...
    return ""


# --- 3. ФУНКЦИИ-ОБРАБОТЧИКИ КОМАНД ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я твой бот для сохранения избранного.\n\n"
        "• /boards - интерактивное меню\n"
        "• /addfile - добавить файл или ссылку\n"
        "• /addboard - создать доску\n\n"
        "Используй /help для полного списка команд."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Управление файлами:*\n"
        "/addfile - Начать процесс добавления файла\n"
        "/view <название> - Получить файл\n"
        "/movefile <название> <доска> - Переместить файл\n"
        "/renamefile <старое> <новое> - Переименовать файл\n"
        "/deletefile <название> - Удалить файл\n\n"
        "*Управление досками:*\n"
        "/boards - Показать все доски (интерактивное меню)\n"
        "/addboard <название> - Создать новую доску\n"
        "/renameboard <старое> <новое> - Переименовать доску\n"
        "/deleteboard <название> - Удалить пустую доску\n\n"
        "/cancel - Отменить текущую операцию",
        parse_mode='Markdown'
    )

# --- Команды для ДОСОК ---
async def addboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Укажи название доски. Пример: /addboard Книги")
        return
    board_name = " ".join(context.args)
    if board_name in get_user_boards(user_id):
        await update.message.reply_text(f"Доска '{board_name}' уже есть.")
        return
    add_board(user_id, board_name)
    await update.message.reply_text(f"✅ Доска '{board_name}' создана!")

async def renameboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if len(context.args) < 2:
        await update.message.reply_text("Формат: /renameboard <старое название> <новое название>")
        return
    
    new_name = context.args[-1]
    old_name = " ".join(context.args[:-1])
    
    if old_name not in get_user_boards(user_id):
        await update.message.reply_text(f"Доска '{old_name}' не найдена.")
        return
    if new_name in get_user_boards(user_id):
        await update.message.reply_text(f"Доска '{new_name}' уже существует.")
        return

    rename_board(user_id, old_name, new_name)
    await update.message.reply_text(f"✅ Доска '{old_name}' переименована в '{new_name}'.")

async def deleteboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Укажи название доски для удаления.")
        return
    board_name = " ".join(context.args)
    if board_name not in get_user_boards(user_id):
        await update.message.reply_text(f"Доска '{board_name}' не найдена.")
        return
    if get_items_in_board(user_id, board_name):
        await update.message.reply_text(f"❌ Нельзя удалить доску '{board_name}', так как она не пуста. Сначала переместите или удалите все файлы из нее.")
        return
    
    if delete_board(user_id, board_name):
        await update.message.reply_text(f"✅ Пустая доска '{board_name}' удалена.")
    else:
        await update.message.reply_text("Произошла ошибка.")

# --- Команды для ФАЙЛОВ ---
async def view_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (код без изменений) ...
    pass

async def movefile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if len(context.args) < 2:
        await update.message.reply_text("Формат: /movefile <название файла> <новая доска>")
        return
    new_board = context.args[-1]
    item_title = " ".join(context.args[:-1])
    if find_item_by_title(user_id, item_title) is None:
        await update.message.reply_text(f"Файл '{item_title}' не найден.")
        return
    if new_board not in get_user_boards(user_id):
        await update.message.reply_text(f"Доска '{new_board}' не существует. Сначала создайте ее.")
        return
    if move_item(user_id, item_title, new_board):
        await update.message.reply_text(f"✅ '{item_title}' перемещен на доску '{new_board}'.")
    else:
        await update.message.reply_text("❌ Ошибка при перемещении.")

async def deletefile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Укажи название файла для удаления.")
        return
    item_title = " ".join(context.args)
    if remove_item(user_id, item_title):
        await update.message.reply_text(f"✅ Файл '{item_title}' удален.")
    else:
        await update.message.reply_text("Файл не найден.")

async def send_item(chat_id: int, item: dict, context: ContextTypes.DEFAULT_TYPE):
    # ... (код без изменений) ...
    pass

async def boards_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (код без изменений) ...
    pass


# --- 4. ФУНКЦИЯ-ОБРАБОТЧИК INLINE-КНОПОК ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (код без изменений, он уже управляет файлами) ...
    pass


# --- 5. ФУНКЦИИ ДЛЯ ДИАЛОГОВ (CONVERSATION HANDLERS) ---
# ... (весь блок с функциями для диалогов остается БЕЗ ИЗМЕНЕНИЙ) ...
async def addfile_start(update, context): pass
async def process_content(update, context): pass
async def get_title(update, context): pass
async def title_callback(update, context): pass
async def ask_board_menu(update, context, is_callback=False): pass
async def board_select_callback(update, context): pass
async def new_board_create_callback(update, context): pass
async def get_new_board_name_and_save(update, context): pass
async def rename_command_start(update, context): pass
async def rename_inline_start(update, context): pass
async def process_new_name(update, context): pass
async def cancel(update, context): pass


# --- 6. ГЛАВНАЯ ФУНКЦИЯ (СБОРКА БОТА) ---

def main():
    """Собирает и запускает бота."""
    initialize_db()
    application = Application.builder().token(BOT_TOKEN).build()
    
    # --- Диалоги ---
    addfile_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("addfile", addfile_start)],
        states={
            WAITING_CONTENT: [MessageHandler(filters.ALL & ~filters.COMMAND, process_content)],
            ASK_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title), CallbackQueryHandler(title_callback, pattern="^use_default_title$")],
            ASK_BOARD: [CallbackQueryHandler(board_select_callback, pattern="^saveboard:"), CallbackQueryHandler(new_board_create_callback, pattern="^create_new_board$")],
            CREATE_BOARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_new_board_name_and_save)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    rename_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("renamefile", rename_command_start), # Изменено на renamefile
            CallbackQueryHandler(rename_inline_start, pattern="^rename_item:")
        ],
        states={
            ASK_NEW_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_new_name)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(addfile_conv_handler)
    application.add_handler(rename_conv_handler)
    
    # --- Команды ---
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Команды для ФАЙЛОВ
    application.add_handler(CommandHandler("view", view_command))
    application.add_handler(CommandHandler("movefile", movefile_command))
    application.add_handler(CommandHandler("deletefile", deletefile_command))

    # Команды для ДОСОК
    application.add_handler(CommandHandler("boards", boards_command))
    application.add_handler(CommandHandler("addboard", addboard_command))
    application.add_handler(CommandHandler("renameboard", renameboard_command))
    application.add_handler(CommandHandler("deleteboard", deleteboard_command))

    # Обработчик кнопок
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Бот запущен...")
    application.run_polling()

# --- 7. ТОЧКА ВХОДА ---
if __name__ == "__main__":
    main()