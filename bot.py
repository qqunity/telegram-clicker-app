from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import json
import asyncio
import nest_asyncio
import os
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse

# Загружаем переменные окружения в самом начале
load_dotenv()

# Применяем патч для event loop
nest_asyncio.apply()

# Словарь для хранения счетчиков пользователей
user_scores = {}
user_multipliers = {}  # Множители для каждого игрока

# Подключение к базе данных
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL не найден в .env файле или переменных окружения")

url = urlparse(DATABASE_URL)
print(url)
connection = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

# Создание таблицы
with connection.cursor() as cursor:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            user_id TEXT PRIMARY KEY,
            score INTEGER DEFAULT 0
        )
    """)
    connection.commit()

# Функция для сохранения данных
async def save_scores():
    with connection.cursor() as cursor:
        for user_id, score in user_scores.items():
            cursor.execute("""
                INSERT INTO scores (user_id, score) 
                VALUES (%s, %s)
                ON CONFLICT (user_id) 
                DO UPDATE SET score = %s
            """, (user_id, score, score))
        connection.commit()

# Функция для загрузки данных
async def load_scores():
    scores = {}
    with connection.cursor() as cursor:
        cursor.execute("SELECT user_id, score FROM scores")
        for user_id, score in cursor.fetchall():
            scores[user_id] = score
    return scores

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global user_scores
    user_id = str(update.effective_user.id)
    
    if user_id not in user_scores:
        user_scores[user_id] = 0
    
    keyboard = [
        [InlineKeyboardButton("Клик! 👆", callback_data="click")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Ваш текущий счет: {user_scores[user_id]}\nНажмите на кнопку, чтобы увеличить счет!",
        reply_markup=reply_markup
    )

# Обработчик нажатия кнопки
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    multiplier = user_multipliers.get(user_id, 1)
    user_scores[user_id] = user_scores.get(user_id, 0) + (1 * multiplier)
    
    # Сохраняем в БД
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO scores (user_id, score) 
            VALUES (%s, %s)
            ON CONFLICT (user_id) 
            DO UPDATE SET score = %s
        """, (user_id, user_scores[user_id], user_scores[user_id]))
        connection.commit()
    
    keyboard = [
        [InlineKeyboardButton("Клик! 👆", callback_data="click")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=f"Ваш текущий счет: {user_scores[user_id]}\nНажмите на кнопку, чтобы увеличить счет!",
        reply_markup=reply_markup
    )

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sorted_scores = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)[:10]
    text = "🏆 Таблица лидеров:\n\n"
    for i, (user_id, score) in enumerate(sorted_scores, 1):
        text += f"{i}. Игрок {user_id}: {score} очков\n"
    
    await update.message.reply_text(text)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    score = user_scores.get(user_id, 0)
    
    await update.message.reply_text(
        f"📊 Ваша статистика:\n"
        f"Очки: {score}\n"
        f"Место в таблице лидеров: {get_rank(user_id)}\n"
    )

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = json.loads(update.effective_message.web_app_data.data)
    user_id = str(update.effective_user.id)
    user_scores[user_id] = data['score']
    await save_scores()
    await update.message.reply_text(f"Ваш счет обновлен: {data['score']}")

async def main():
    global user_scores
    # Загружаем сохраненные данные
    user_scores = await load_scores()
    
    token = os.getenv('BOT_TOKEN')
    if not token:
        raise ValueError("BOT_TOKEN не найден в .env файле или переменных окружения")
        
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))

    print("Бот запущен. Нажмите Ctrl+C для остановки")
    
    # Запускаем бота и держим его активным
    await application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nБот остановлен") 