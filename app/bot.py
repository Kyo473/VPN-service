import logging
from aiogram import Bot, Dispatcher, types, Router
from aiogram.enums import ParseMode
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import F
import aiohttp
import asyncio

from app.config import BOT_TOKEN, API_SECRET_TOKEN, API_URL, ADMIN_IDS

# Создание объектов
bot = Bot(token=BOT_TOKEN, default=types.DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# FSM
class Form(StatesGroup):
    waiting_for_action = State()
    waiting_for_email = State()
    waiting_for_delete_email = State()

# Клавиатуры
start_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="🆓 Пробный ключ")],
    [KeyboardButton(text="💳 Приобрести подписку")],
], resize_keyboard=True)

admin_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="📋 Все пользователи")],
    [KeyboardButton(text="➕ Выдать ключ")],
    [KeyboardButton(text="❌ Удалить ключ")],
], resize_keyboard=True)

# /start
@router.message(F.text == "/start")
async def start_handler(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMIN_IDS:
        await message.answer("Добро пожаловать в админ-панель", reply_markup=admin_keyboard)
    else:
        await message.answer("Привет! Что ты хочешь сделать?", reply_markup=start_keyboard)
        await state.set_state(Form.waiting_for_action)

# выбор действия
@router.message(Form.waiting_for_action)
async def user_choice(message: types.Message, state: FSMContext):
    if message.text in ["🆓 Пробный ключ", "💳 Приобрести подписку"]:
        await message.answer("Введите ваш email:")
        await state.set_state(Form.waiting_for_email)
    else:
        await message.answer("Пожалуйста, выбери один из пунктов меню.")

# ввод email для получения ключа
@router.message(Form.waiting_for_email)
async def email_input(message: types.Message, state: FSMContext):
    email = message.text.strip()
    await state.clear()
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}", params={"email": email, "token": API_SECRET_TOKEN}) as r:
            if r.status == 200:
                json_data = await r.json()
                await message.answer(f"✅ Ваш ключ:\n<code>{json_data['link']}</code>")
            else:
                await message.answer("❌ Ошибка при создании ключа. Возможно, он уже существует.")

# admin: все пользователи
@router.message(F.text == "📋 Все пользователи")
async def list_keys(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL.replace('/add-user', '/all-users')}", params={"token": API_SECRET_TOKEN}) as r:
            if r.status == 200:
                users = await r.json()
                if users:
                    text = "\n".join([f"- {u['email']}" for u in users])
                    await message.answer(f"👥 Все пользователи:\n{text}")
                else:
                    await message.answer("Список пуст")
            else:
                await message.answer("Ошибка API")

# admin: вручную выдать
@router.message(F.text == "➕ Выдать ключ")
async def manual_add(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("Введите email для выдачи:")
    await state.set_state(Form.waiting_for_email)

# admin: удалить ключ
@router.message(F.text == "❌ Удалить ключ")
async def delete_key_prompt(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("Введи email, который нужно удалить:")
    await state.set_state(Form.waiting_for_delete_email)

@router.message(Form.waiting_for_delete_email)
async def delete_key_action(message: types.Message, state: FSMContext):
    email = message.text.strip()
    await state.clear()
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL.replace('/add-user', '/delete-user')}", params={"email": email, "token": API_SECRET_TOKEN}) as r:
            if r.status == 200:
                data = await r.json()
                if data.get("success"):
                    await message.answer("✅ Ключ удалён.")
                else:
                    await message.answer("⚠️ Пользователь не найден.")
            else:
                await message.answer("Ошибка при удалении.")

# fallback
@router.message()
async def fallback(message: types.Message):
    await message.answer("Неизвестная команда. Используй /start")

# запуск
async def main():
    logging.basicConfig(level=logging.INFO)
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
