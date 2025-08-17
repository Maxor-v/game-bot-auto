import asyncio
import random

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import TOKEN
import sqlite3
import logging
import requests

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

button_registr = KeyboardButton(text="Регистрация в телеграм боте")
button_exchange_rates = KeyboardButton(text="Курс валют")
button_tips = KeyboardButton(text="Советы по экономии")
button_finances = KeyboardButton(text="Личные финансы")
button_wiev_finances = KeyboardButton(text="Посмотреть финансы")

keyboards = ReplyKeyboardMarkup(keyboard=[
   [button_registr, button_exchange_rates],
   [button_tips, button_finances],
   [button_wiev_finances]
   ], resize_keyboard=True)

conn = sqlite3.connect('user.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
   id INTEGER PRIMARY KEY,
   telegram_id INTEGER UNIQUE,
   name TEXT,
   category1 TEXT,
   category2 TEXT,
   category3 TEXT,
   expenses1 REAL,
   expenses2 REAL,
   expenses3 REAL
   )
''')

conn.commit()

class FinancesForm(StatesGroup):
   category1 = State()
   expenses1 = State()
   category2 = State()
   expenses2 = State()
   category3 = State()
   expenses3 = State()


@dp.message(Command('start'))
async def send_start(message: Message):
   await message.answer("Привет! Я ваш личный финансовый помощник. Выберите одну из опций в меню:", reply_markup=keyboards)

@dp.message(F.text == "Регистрация в телеграм боте")
async def registration(message: Message):
   telegram_id = message.from_user.id
   name = message.from_user.full_name
   cursor.execute('''SELECT * FROM users WHERE telegram_id = ?''', (telegram_id,))
   user = cursor.fetchone()
   if user:
       await message.answer("Вы уже зарегистрированы!")
   else:
       cursor.execute('''INSERT INTO users (telegram_id, name) VALUES (?, ?)''', (telegram_id, name))
       conn.commit()
       await message.answer("Вы успешно зарегистрированы!")


def get_user_data_for_bot(telegram_id: int) -> str:
    """Возвращает форматированную строку с данными пользователя"""
    try:
        #conn = sqlite3.connect('your_database.db')
        #cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        user_data = cursor.fetchone()

        if not user_data:
            return f"❌ Пользователь не найден"

        (_, _, name, cat1, cat2, cat3, exp1, exp2, exp3) = user_data

        message = [
            f"📊 <b>Ваша статистика:</b>",
            f"👤 <b>Имя:</b> {name or 'Не указано'}",
            "",
            "💳 <b>Категории расходов:</b>",
            f"1. {cat1 or 'Без категории'}: {exp1 or 0:.2f} ₽",
            f"2. {cat2 or 'Без категории'}: {exp2 or 0:.2f} ₽",
            f"3. {cat3 or 'Без категории'}: {exp3 or 0:.2f} ₽"
        ]

        return "\n".join(message)

    except sqlite3.Error as e:
        return f"⚠️ Ошибка базы данных: {e}"


@dp.message(F.text == "Посмотреть финансы")
async def wiev_finance(message: Message):
    await message.answer(get_user_data_for_bot(message.from_user.id), parse_mode='HTML')


@dp.message(F.text == "Курс валют")
async def exchange_rates(message: Message):
   url = "https://v6.exchangerate-api.com/v6/09edf8b2bb246e1f801cbfba/latest/USD"
   try:
       response = requests.get(url)
       data = response.json()
       if response.status_code != 200:
           await message.answer("Не удалось получить данные о курсе валют!")
           return
       usd_to_rub = data['conversion_rates']['RUB']
       eur_to_usd = data['conversion_rates']['EUR']

       euro_to_rub =  usd_to_rub / eur_to_usd
       await message.answer(f"1 USD - {usd_to_rub:.2f}  RUB\n"
                            f"1 EUR - {euro_to_rub:.2f}  RUB")


   except:
       await message.answer("Произошла ошибка")

@dp.message(F.text == "Советы по экономии")
async def send_tips(message: Message):
   tips = [
       "Совет 1: Ведите бюджет и следите за своими расходами.",
       "Совет 2: Откладывайте часть доходов на сбережения.",
       "Совет 3: Покупайте товары по скидкам и распродажам."
   ]
   tip = random.choice(tips)
   await message.answer(tip)

@dp.message(F.text == "Личные финансы")
async def finances(message: Message, state: FSMContext):
   await state.set_state(FinancesForm.category1)
   await message.reply("Введите первую категорию расходов:")

@dp.message(FinancesForm.category1)
async def finances(message: Message, state: FSMContext):
   await state.update_data(category1 = message.text)
   await state.set_state(FinancesForm.expenses1)
   await message.reply("Введите расходы для категории 1:")

@dp.message(FinancesForm.expenses1)
async def finances(message: Message, state: FSMContext):
   await state.update_data(expenses1 = float(message.text))
   await state.set_state(FinancesForm.category2)
   await message.reply("Введите вторую категорию расходов:")

@dp.message(FinancesForm.category2)
async def finances(message: Message, state: FSMContext):
   await state.update_data(category2 = message.text)
   await state.set_state(FinancesForm.expenses2)
   await message.reply("Введите расходы для категории 2:")

@dp.message(FinancesForm.expenses2)
async def finances(message: Message, state: FSMContext):
   await state.update_data(expenses2 = float(message.text))
   await state.set_state(FinancesForm.category3)
   await message.reply("Введите третью категорию расходов:")

@dp.message(FinancesForm.category3)
async def finances(message: Message, state: FSMContext):
   await state.update_data(category3 = message.text)
   await state.set_state(FinancesForm.expenses3)
   await message.reply("Введите расходы для категории 3:")

@dp.message(FinancesForm.expenses3)
async def finances(message: Message, state: FSMContext):
   data = await state.get_data()
   telegarm_id = message.from_user.id
   cursor.execute('''UPDATE users SET category1 = ?, expenses1 = ?, category2 = ?, expenses2 = ?, category3 = ?, expenses3 = ? WHERE telegram_id = ?''',
                  (data['category1'], data['expenses1'], data['category2'], data['expenses2'], data['category3'], float(message.text), telegarm_id))
   conn.commit()
   await state.clear()

   await message.answer("Категории и расходы сохранены!")


async def main():
   await dp.start_polling(bot)

if __name__ == '__main__':
   asyncio.run(main())



