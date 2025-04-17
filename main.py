import os
import random
import json
import time
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.daily import DailyTrigger

# Получаем данные из переменных окружения
TOKEN = os.getenv('TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
PORT = os.getenv('PORT')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Загадки и рейтинг
puzzles = json.loads(open("puzzles.json", "r", encoding="utf-8").read())
users_data = {}

# Функция для отправки загадки
async def send_puzzle():
    today = datetime.now().date()
    puzzle_data = next((item for item in puzzles if item["date"] == str(today)), None)
    if puzzle_data:
        question = puzzle_data["question"]
        hint = puzzle_data["hint"]
        correct_answer = puzzle_data["answer"].lower()
        for user_id in users_data.keys():
            if 'answer' not in users_data[user_id]:
                await bot.send_message(user_id, f"Загадка дня: {question}\nОтветьте на неё как можно быстрее!\n\n💡 Подсказка: {hint}")
        return correct_answer
    else:
        return None

# Функция для обновления НИТИкоинов
def update_niti_coins(user_id, amount):
    if user_id not in users_data:
        users_data[user_id] = {"coins": 0}
    users_data[user_id]["coins"] += amount

# Функция для генерации таймера до следующей загадки
def get_time_until_next_puzzle():
    now = datetime.now()
    next_puzzle_time = datetime(now.year, now.month, now.day, 9, 0, 0) + timedelta(days=1)
    return next_puzzle_time - now

# Обработчик команды /start
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users_data:
        users_data[user_id] = {"coins": 0, "answered": False, "hint_used": False}
    
    # Отправляем приветствие
    await message.answer(f"Привет, {message.from_user.first_name}! 🎉\n\n"
                         f"Молодежный совет НИТИ приветствует тебя! Мы уверены, что ты сможешь разгадать наши загадки. 🧠"
                         f" Загадка дня будет доступна в 09:00 по Москве. Желаем тебе побольше НИТИкоинов! 💰\n\n"
                         f"Твоя задача: отгадывать загадки и зарабатывать НИТИкоины. 😎")

    # Присылаем загадку сразу
    correct_answer = await send_puzzle()

    # Обработчик кнопок
@dp.message_handler(commands=['mycoins'])
async def my_coins(message: types.Message):
    user_id = message.from_user.id
    if user_id in users_data:
        coins = users_data[user_id]["coins"]
        await message.answer(f"Твои НИТИкоины: {coins} 💰")
    else:
        await message.answer("Ты ещё не начал играть. Приходи каждый день и получай загадки! 😇")

@dp.message_handler(commands=['hint'])
async def hint(message: types.Message):
    user_id = message.from_user.id
    if user_id in users_data and not users_data[user_id]["hint_used"]:
        users_data[user_id]["hint_used"] = True
        await message.answer(f"Подсказка: {puzzles[0]['hint']}")
    else:
        await message.answer("Подсказка доступна только через 30 минут после загадки! ⏳")

# Обработчик команд администратора
@dp.message_handler(commands=['commands'])
async def show_commands(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Доступные команды:\n"
                             "/start - начать игру\n"
                             "/mycoins - узнать свои НИТИкоины\n"
                             "/hint - получить подсказку (доступна через 30 мин)\n"
                             "/commands - показать команды (только для админа)\n"
                             "/addpuzzle - добавить новую загадку\n")

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
