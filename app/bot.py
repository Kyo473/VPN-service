import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InputFile
from aiogram.filters import CommandStart
import requests
import qrcode
import io
from app.config import BOT_TOKEN, API_SECRET_TOKEN

API_URL = "http://api:8000/add-user"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    email = message.from_user.username or f"user{message.from_user.id}"
    response = requests.get(API_URL, params={"email": email, "token": API_SECRET_TOKEN}).json()

    if "error" in response:
        await message.answer("❌ Такой пользователь уже существует.")
        return

    link = response["link"]

    # Генерация QR
    qr = qrcode.make(link)
    bio = io.BytesIO()
    qr.save(bio, format="PNG")
    bio.name = "qr.png"
    bio.seek(0)

    await message.answer_photo(
        photo=InputFile(bio),
        caption=f"✅ Ваш VPN:\n`{link}`",
        parse_mode="Markdown"
    )

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
