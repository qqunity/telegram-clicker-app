from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import json
import asyncio
import nest_asyncio
import os
from dotenv import load_dotenv
from database import Database
from server import start_server
from game_repository import GameRepository

# Загружаем переменные окружения в самом начале
load_dotenv()

# Запускаем веб-сервер в отдельном потоке
start_server()

# Применяем патч для event loop
nest_asyncio.apply()

# Словарь для хранения счетчиков пользователей
user_scores = {}
user_multipliers = {}  # Множители для каждого игрока

# Удаляем старый код подключения к БД
db = Database.get_instance()

game_repo = GameRepository()

# Функция для сохранения данных
async def save_scores():
    conn = db.get_connection()
    if not conn:
        return
        
    with conn.cursor() as cursor:
        for user_id, score in user_scores.items():
            multiplier = user_multipliers.get(user_id, 1)
            cursor.execute("""
                INSERT INTO scores (user_id, score, multiplier) 
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id) 
                DO UPDATE SET score = %s, multiplier = %s
            """, (user_id, score, multiplier, score, multiplier))
        conn.commit()

# Функция для загрузки данных
async def load_scores():
    scores = {}
    multipliers = {}
    conn = db.get_connection()
    if not conn:
        return scores, multipliers
    
    with conn.cursor() as cursor:
        cursor.execute("SELECT user_id, score, multiplier FROM scores")
        for user_id, score, multiplier in cursor.fetchall():
            scores[user_id] = score
            multipliers[user_id] = multiplier
    return scores, multipliers

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    webapp_button = InlineKeyboardButton(
        text="🎮 Играть", 
        web_app=WebAppInfo(url=f"https://qqunity.ru")
    )
    stats_button = InlineKeyboardButton("📊 Статистика", callback_data="stats")
    keyboard = InlineKeyboardMarkup([[webapp_button], [stats_button]])
    
    await update.message.reply_text(
        "🎮 Добро пожаловать в Telegram Кликер!\n\n"
        "Нажимайте на кнопку, чтобы заработать очки.\n"
        "Каждые 100 очков ваш множитель будет расти!",
        reply_markup=keyboard
    )

# Обработчик нажатия кнопки
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    try:
        current_data = game_repo.get_user_score(user_id) or (0, 1)
        score, multiplier = current_data
        
        score += multiplier
        game_repo.save_score(user_id, score, multiplier)
        
        keyboard = [
            [InlineKeyboardButton("Клик! 👆", callback_data="click")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=f"Ваш текущий счет: {score}\nНажмите на кнопку, чтобы увеличить счет!",
            reply_markup=reply_markup
        )
    except Exception as e:
        print(f"Ошибка при обработке клика: {e}")
        await query.answer("Произошла ошибка при сохранении прогресса")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        leaders = game_repo.get_leaderboard(10)
        text = "🏆 Таблица лидеров:\n\n"
        for i, (user_id, score, multiplier) in enumerate(leaders, 1):
            text += f"{i}. Игрок {user_id}: {score} очков (x{multiplier})\n"
        
        await update.message.reply_text(text)
    except Exception as e:
        print(f"Ошибка при получении таблицы лидеров: {e}")
        await update.message.reply_text("Не удалось загрузить таблицу лидеров")

async def get_rank(user_id: str) -> int:
    try:
        leaders = game_repo.get_leaderboard()
        for i, (leader_id, _, _) in enumerate(leaders, 1):
            if leader_id == user_id:
                return i
        return len(leaders) + 1
    except Exception:
        return 0

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.effective_user.id)
        user_data = game_repo.get_user_score(user_id)
        
        if user_data:
            score, multiplier = user_data
            rank = await get_rank(user_id)
            
            await update.message.reply_text(
                f"📊 Ваша статистика:\n"
                f"Очки: {score}\n"
                f"Множитель: x{multiplier}\n"
                f"Место в таблице лидеров: {rank}\n"
            )
        else:
            await update.message.reply_text(
                "📊 У вас пока нет очков.\n"
                "Начните игру, чтобы заработать первые очки!"
            )
    except Exception as e:
        print(f"Ошибка при получении статистики: {e}")
        await update.message.reply_text("Не удалось загрузить статистику")

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = json.loads(update.effective_message.web_app_data.data)
        user_id = str(update.effective_user.id)
        
        game_repo.save_score(
            user_id=user_id,
            score=data['score'],
            multiplier=data.get('multiplier', 1)
        )
        
        await update.message.reply_text(
            f"🎮 Игра сохранена!\n"
            f"📊 Ваш счет: {data['score']}\n"
            f"✨ Множитель: x{data.get('multiplier', 1)}"
        )
    except Exception as e:
        print(f"Ошибка при обработке данных от веб-приложения: {e}")
        await update.message.reply_text("Произошла ошибка при сохранении прогресса")

async def main():
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
    
    await application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nБот остановлен") 