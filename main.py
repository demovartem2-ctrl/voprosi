import asyncio
import logging
import os
import random

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.types import Message

# --- Настройки ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "1780243336:u34zqUIG9LxtW9-ig_m5jOsCvpBqU-fO-V4")
API_BASE = os.getenv("API_BASE", "https://misugram.cloud-ip.cc")
PORT = int(os.getenv("PORT", "8080"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("yesno-bot")

# --- Aiogram через кастомный Bot API ---
session = AiohttpSession(api=TelegramAPIServer.from_base(API_BASE))
bot = Bot(token=BOT_TOKEN, session=session)
dp = Dispatcher()


@dp.message(F.text)
async def yes_no(message: Message) -> None:
    text = (message.text or "").strip()
    if text.endswith("?"):
        answer = random.choice(["да", "нет"])
        await message.reply(answer)


async def start_health_server() -> None:
    """Render ждёт открытый порт — отдаём /healthz."""
    app = web.Application()
    app.router.add_get("/", lambda _: web.Response(text="ok"))
    app.router.add_get("/healthz", lambda _: web.Response(text="ok"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    log.info("health server on 0.0.0.0:%s", PORT)


async def main() -> None:
    await start_health_server()
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:  # кастомный API может не знать метод — не падаем
        log.warning("delete_webhook failed: %s", e)

    log.info("polling started via %s", API_BASE)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("stopped")
