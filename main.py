import logging
import os

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.storage import MemoryStorage
from aiogram.middleware.logging import LoggingMiddleware
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.utils.helper import Helper, HelperMode, ListItem
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

class Purchase(StatesGroup):
    sum = State()
    payment_method = State()

binance = ccxt.binance({
    "apiKey": BINANCE_API_KEY,
    "secret": BINANCE_SECRET_KEY,
})

def get_btc_rub_price():
    ticker = binance.fetch_ticker("BTC/RUB")
    return ticker["ask"]

markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
markup.add("Купить BTC", "Продать BTC")

@dp.message_handler(Text(equals="/start"))
async def cmd_start(message: types.Message):
    await message.reply("Добро пожаловать в Simple BTC!\nВыберите действие:", reply_markup=markup)

@dp.message_handler(lambda message: message.text == "Купить BTC")
async def buy_btc(message: types.Message):
    await message.reply("Укажите сумму в BTC или RUB:\n\nПример: 0.001 или 0,001 или 3940\n\nМинимальная сумма для обмена 1000 рублей или 0,0005 btc")
    await Purchase.sum.set()

@dp.message_handler(lambda message: message.text, state=Purchase.sum)
async def process_sum(message: types.Message, state):
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
    elif 0.0005 <= sum_value < 1000 / float(get_btc_rub_price()):
        await state.update_data(btc_amount=sum_value)
    else:
        await message.reply("Сумма должна быть минимум 1000 рублей или 0,0005 BTC.")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Сбербанк", "Тинькофф", "QIWI")
    await message.reply("Выберите метод оплаты:", reply_markup=markup)
    await Purchase.payment_method.set()

@dp.message_handler(lambda message: message.text in ["Сбербанк", "Тинькофф", "QIWI"], state=Purchase.payment_method)
async def process_payment_method(message: types.Message, state):
    user_data = await state.get_data()
    btc_amount = user_data["btc_amount"]
    payment_method = message.text

    details = payment_details[payment_method]
    await message.reply(f"Вы выбрали {payment_method}.\n\n{details}\n\nК оплате: {btc_amount:.8f} BTC\n\nПосле оплаты, обратитесь в поддержку @Pav_Glash")
    await state.finish()

@dp.message_handler(lambda message: message.text == "Продать BTC")
async def sell_btc(message: types.Message):
    await message.reply("Функция продажи BTC временно недоступна.")

payment_details = {
    "Сбербанк": "Номер карты: 1234 5678 1234 5678\nИмя: Иван Иванов\n",
    "Тинькофф": "Номер карты: 2345 6789 2345 6789\nИмя: Иван Иванов\n",
    "QIWI": "Номер телефона: +7 123 456 78 90\n",
}

if __name__ == "__main__":
    from aiogram import executor
    from handlers import dp

    executor.start_polling(dp, skip_updates=True)
