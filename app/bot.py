import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import F
import aiohttp
import asyncio
import os
from app import BOT_TOKEN, API_SECRET_TOKEN, API_URL, ADMIN_IDS

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

class Form(StatesGroup):
    waiting_for_action = State()
    waiting_for_email = State()

start_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="🆓 Пробный ключ")],
    [KeyboardButton(text="💳 Приобрести подписку")],
], resize_keyboard=True)

admin_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="📋 Все пользователи")],
    [KeyboardButton(text="➕ Выдать ключ")],
    [KeyboardButton(text="❌ Удалить ключ")],
], resize_keyboard=True)

@dp.message(F.text == "/start")
async def start_handler(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMIN_IDS:
        await message.answer("Добро пожаловать в админ-панель", reply_markup=admin_keyboard)
    else:
        await message.answer("Привет! Что ты хочешь сделать?", reply_markup=start_keyboard)
        await state.set_state(Form.waiting_for_action)

@dp.message(Form.waiting_for_action)
async def user_choice(message: types.Message, state: FSMContext):
    if message.text == "🆓 Пробный ключ" or message.text == "💳 Приобрести подписку":
        await message.answer("Введите ваш email:")
        await state.set_state(Form.waiting_for_email)
    else:
        await message.answer("Пожалуйста, выбери один из пунктов меню.")

@dp.message(Form.waiting_for_email)
async def email_input(message: types.Message, state: FSMContext):
    email = message.text.strip()
    await state.clear()
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/add-user", params={"email": email, "token": API_SECRET_TOKEN}) as r:
            if r.status == 200:
                json_data = await r.json()
                await message.answer(f"✅ Ваш ключ:\n<code>{json_data['link']}</code>")
            else:
                await message.answer("Ошибка при создании ключа. Возможно, он уже существует.")

@dp.message(F.text == "📋 Все пользователи")
async def list_keys(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/all-users", params={"token": API_SECRET_TOKEN}) as r:
            if r.status == 200:
                users = await r.json()
                if users:
                    text = "\n".join([f"- {u['email']}" for u in users])
                    await message.answer(f"👥 Все пользователи:\n{text}")
                else:
                    await message.answer("Список пуст")
            else:
                await message.answer("Ошибка API")

@dp.message(F.text == "➕ Выдать ключ")
async def manual_add(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("Введите email для выдачи:")
    await state.set_state(Form.waiting_for_email)

@dp.message(F.text == "❌ Удалить ключ")
async def delete_key(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("Введи email, который нужно удалить:")
    await dp.fsm.set_state(message.from_user.id, Form.waiting_for_email.state)

@dp.message()
async def fallback(message: types.Message):
    await message.answer("Неизвестная команда. Используй /start")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import asyncio
    from aiogram import executor

    asyncio.run(dp.start_polling(bot))
