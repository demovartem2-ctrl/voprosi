import asyncio
import logging
import os
import random

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ChatType
from aiogram.types import Message

BOT_TOKEN = os.getenv("BOT_TOKEN", "1780243336:u34zqUIG9LxtW9-ig_m5jOsCvpBqU-fO-V4")
API_BASE = os.getenv("API_BASE", "https://misugram.cloud-ip.cc")
PORT = int(os.getenv("PORT", "8080"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("yesno-bot")

session = AiohttpSession(api=TelegramAPIServer.from_base(API_BASE))
bot = Bot(token=BOT_TOKEN, session=session)
dp = Dispatcher()


def extract_text(message: Message) -> str:
    """Текст сообщения или подпись к фото/видео/файлу."""
    return (message.text or message.caption or "").strip()


def clean_for_match(text: str, bot_username: str | None) -> str:
    """Убирает @упоминание бота в конце, чтобы 'Пойдём?@bot' тоже срабатывал."""
    if bot_username:
        text = text.replace(f"@{bot_username}", "").strip()
    return text


@dp.message(F.text | F.caption)
async def yes_no(message: Message) -> None:
    text = extract_text(message)
    if not text:
        return

    me = await bot.me()
    text = clean_for_match(text, me.username)

    # в группах не отвечаем на команды типа /start
    if text.startswith("/"):
        return

    if text.endswith("?"):
        answer = random.choice(["да", "нет"])
        await message.reply(answer)


@dp.edited_message(F.text | F.caption)
async def yes_no_edited(message: Message) -> None:
    text = extract_text(message)
    if not text:
        return
    me = await bot.me()
    text = clean_for_match(text, me.username)
    if text.startswith("/"):
        return
    if text.endswith("?"):
        await message.reply(random.choice(["да", "нет"]))


@dp.message(F.new_chat_members)
async def on_added(message: Message) -> None:
    """Приветствие при добавлении в группу."""
    me = await bot.me()
    for member in message.new_chat_members or []:
        if member.id == me.id:
            await message.answer(
                "Привет! Я отвечаю «да»/«нет» на любой вопрос, "
                "который заканчивается на «?».\n"
                "Например: «Пойдём гулять?»"
            )
            break


@dp.my_chat_member()
async def on_membership(event) -> None:
    log.info("membership change: chat=%s status=%s",
             event.chat.id, event.new_chat_member.status)


async def start_health_server() -> None:
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
    except Exception as e:
        log.warning("delete_webhook failed: %s", e)

    me = await bot.me()
    log.info("polling as @%s via %s", me.username, API_BASE)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("stopped")
