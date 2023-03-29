import os
import logging
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.utils import executor
from aiogram.utils.markdown import text, escape_md
from binance.client import Client
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("5683212966:AAFROD7629pEwgVHLOGyWap0vtKdxN3EdHE")
CHAT_ID = int(os.getenv("358968367"))

binance_api_key = os.getenv("zX6iKEIMBXY9dJyyz2a1etoKCEYcVtrAI4JqPrvc0ihVQWxGDCZyNYBpMiGOR66w")
binance_api_secret = os.getenv("s80evkPVnOF6kk6nDkN1UwdyQdB446M3pxsSbaZtostVn2j34i8vSU3BuQjG3EF")

binance_client = Client(binance_api_key, binance_api_secret)

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Реквизиты для оплаты
payment_details = {
    "Сбербанк": "Номер карты: 1234 5678 9012 3456\nИмя получателя: Иван Иванов",
    "Тинькофф": "Номер карты: 2345 6789 0123 4567\nИмя получателя: Петр Петров",
    "QIWI": "Номер кошелька: +79991234567\nИмя получателя: Сергей Сергеев",
}

def get_btc_rub_price():
    ticker = binance_client.get_ticker_price(symbol="BTCRUB")
    btc_rub_price = float(ticker["price"])
    return btc_rub_price

markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
markup.add("Купить BTC", "Продать BTC", "Поддержка")

from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.middlewares.logging import LoggingMiddleware

class Purchase(StatesGroup):
    sum = State()
    payment_method = State()

class Sale(StatesGroup):
    sum = State()

@dp.message_handler(Command("start"))
async def cmd_start(message: types.Message):
    await message.reply("Добро пожаловать в Simple BTC!\nВыберите действие:", reply_markup=markup)

@dp.message_handler(lambda message: message.text == "Купить BTC")
async def buy_btc(message: types.Message):
    await message.reply("Укажите сумму в BTC или RUB:\n\nПример: 0.001 или 0,001 или 3940\n\nМинимальная сумма для обмена 1000 рублей или 0,0005 btc")
    await Purchase.sum.set()

async def process_sum(message: types.Message, state: FSMContext):
    user_input = message.text.replace(',', '.')
    try:
        sum_value = float(user_input)
    except ValueError:
        await message.reply("Сумма должна быть числом. Пожалуйста, введите сумму еще раз.")
        return

    if sum_value >= 1000:
        btc_rub_price = get_btc_rub_price()
        btc_amount = sum_value / btc_rub_price * 0.85
        await state.update_data(btc_amount=btc_amount)
    elif 0.0005 <= sum_value < 1000/float(get_btc_rub_price()):
        await state.update_data(btc_amount=sum_value)
    else:
        await message.reply("Сумма должна быть минимум 1000 рублей или 0,0005 BTC.")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Сбербанк", "Тинькофф", "QIWI")
    await message.reply("Выберите метод оплаты:", reply_markup=markup)
    await Purchase.payment_method.set()

@dp.message_handler(lambda message: message.text in ["Сбербанк", "Тинькофф", "QIWI"], state=Purchase.payment_method)
async def process_payment_method(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    btc_amount = user_data["btc_amount"]
    payment_method = message.text

    details = payment_details[payment_method]
    await message.reply(f"Вы выбрали {payment_method}.\n\n{details}\n\nК оплате: {btc_amount:.8f} BTC\n\nПосле оплаты, обратитесь в поддержку @Pav_Glash")
    await state.finish()

@dp.message_handler(lambda message: message.text == "Продать BTC")
async def sell_btc(message: types.Message):
    await message.reply("Функция продажи BTC временно недоступна.")

@dp.message_handler(lambda message: message.text == "Поддержка")
async def support(message: types.Message):
    await message.reply("Если у вас возникли вопросы или проблемы, обратитесь к @Pav_Glash")

async def on_startup(dp):
    await bot.send_message(chat_id=CHAT_ID, text="Бот запущен")

async def on_shutdown(dp):
    await bot.send_message(chat_id=CHAT_ID, text="Бот остановлен")

    await bot.close()

if __name__ == "__main__":
    from aiogram import executor

    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)
