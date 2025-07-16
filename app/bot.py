from aiogram import Bot, Dispatcher, types
from aiogram.types import InputFile
from aiogram.utils import executor
import qrcode
import io
import requests
from app.config import BOT_TOKEN, API_SECRET_TOKEN

API_URL = "http://api:8000/add-user"  # внутренняя точка

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    email = message.from_user.username or f"user{message.from_user.id}"
    response = requests.get(API_URL, params={"email": email, "token": API_SECRET_TOKEN}).json()

    if "error" in response:
        await message.answer("❌ Такой пользователь уже существует.")
        return

    link = response["link"]

    # Генерация QR
    qr = qrcode.make(link)
    bio = io.BytesIO()
    bio.name = "qr.png"
    qr.save(bio, "PNG")
    bio.seek(0)

    await message.answer_photo(
        photo=InputFile(bio),
        caption=f"✅ Ваш VPN:\n`{link}`",
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
