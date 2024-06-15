import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from database import SessionLocal, create_user, get_user, update_balance, initialize_users
from config import ngrok_url, TOKEN, ADMIN_USER_IDS




'''hehe wwqix'''




API_TOKEN = TOKEN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    '''функция приветствует пользователя и добавляет его id, first_name в бд'''
    logger.info(f"Received /start command from user {message.from_user.id}")
    db = SessionLocal()
    user = get_user(db, message.from_user.id)
    if not user:
        create_user(db, message.from_user.id, message.from_user.first_name)
        initialize_users(db)


    web_app_url = f"{ngrok_url}/?user_id={message.from_user.id}"
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("💰Старт", web_app=types.WebAppInfo(url=web_app_url))
    )
    await message.answer(f"👋 Привет, @{message.from_user.username}!\n\nЧтобы начать, просто нажми на кнопку ниже 👇", reply_markup=keyboard)


@dp.message_handler(commands=['add_balance'])
async def cmd_add_balance(message: types.Message):
    '''админ функция для добавления 🥮 на баланс пользователя'''
    if message.from_user.id not in ADMIN_USER_IDS:
        await message.reply("У вас недостаточно прав для использования данной команды")
        return

    args = message.text.split()
    if len(args) != 3:
        await message.reply("Ипользуйте команду: /add_balance <id_пользователя> <количество>")
        return

    user_id = int(args[1])
    amount = int(args[2])

    db = SessionLocal()
    user = get_user(db, user_id)
    if user:
        user.balance += amount
        db.commit()
        await message.reply(f"Добавлено {amount} 🥮 пользователю {user_id}. Новый баланс: {user.balance}")
    else:
        await message.reply(f"Пользователь {user_id} не найден.")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

