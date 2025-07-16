from pyrogram import Client, filters
from pyrogram.types import Message
import requests
import qrcode
import io
from config import API_SECRET_TOKEN, BOT_TOKEN

API_URL = "http://api:8000/add-user" 

bot = Client("vpn_bot", bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start"))
async def start(client, message: Message):
    email = message.from_user.username or f"user{message.from_user.id}"
    response = requests.get(API_URL, params={"email": email, "token": API_SECRET_TOKEN}).json()

    if "error" in response:
        await message.reply("❌ Такой пользователь уже существует.")
        return

    link = response["link"]
    qr = qrcode.make(link)
    bio = io.BytesIO()
    bio.name = "qr.png"
    qr.save(bio, "PNG")
    bio.seek(0)

    await message.reply_photo(
        photo=bio,
        caption=f"✅ Ваш конфиг:\n`{link}`",
        parse_mode="markdown"
    )

bot.run()
