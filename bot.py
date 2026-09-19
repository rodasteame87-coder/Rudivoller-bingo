import os
import asyncio
import threading

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
APP_URL = os.environ.get(
    "APP_URL",
    "https://rudivoller-bingo.onrender.com"
)

ADMIN_USER_ID = os.environ.get("ADMIN_USER_ID", "")


def is_admin(user_id):
    return ADMIN_USER_ID and str(user_id) == str(ADMIN_USER_ID)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton(
                "🎮 Open Bingo",
                web_app=WebAppInfo(url=APP_URL)
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🎯 *Rudivoller Bingo*\n\n"
        "Welcome to Rudivoller Bingo!\n\n"
        "Tap the button below to enter the game.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def bingo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton(
                "🎮 Open Bingo",
                web_app=WebAppInfo(url=APP_URL)
            )
        ]
    ]

    await update.message.reply_text(
        "🎯 Tap below to enter Rudivoller Bingo:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only.")
        return

    from server import game, lock

    with lock:
        game["running"] = True
        game["called"] = []
        game["winners"] = []

    await update.message.reply_text(
        "🟢 *Bingo game started!*\n\n"
        "Players can now enter the game.",
        parse_mode="Markdown"
    )


async def stopgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only.")
        return

    from server import game, lock

    with lock:
        game["running"] = False

    await update.message.reply_text("🔴 Bingo game stopped.")


async def call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only.")
        return

    from server import game, lock

    with lock:

        if not game["running"]:
            await update.message.reply_text(
                "❌ The game is not running."
            )
            return

        available = [
            n for n in range(1, 76)
            if n not in game["called"]
        ]

        if not available:
            game["running"] = False

            await update.message.reply_text(
                "🏁 All 75 numbers have been called."
            )
            return

        number = available[0]

        # Random number
        import random
        number = random.choice(available)

        game["called"].append(number)

        if number <= 15:
            letter = "B"
        elif number <= 30:
            letter = "I"
        elif number <= 45:
            letter = "N"
        elif number <= 60:
            letter = "G"
        else:
            letter = "O"

    await update.message.reply_text(
        f"🎱 *{letter}-{number}*",
        parse_mode="Markdown"
    )


async def state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from server import game, lock

    with lock:
        running = game["running"]
        called = list(game["called"])
        players = len(game["players"])
        winners = list(game["winners"])

    await update.message.reply_text(
        "🎯 *Rudivoller Bingo Status*\n\n"
        f"Game: {'🟢 LIVE' if running else '🔴 STOPPED'}\n"
        f"Players: {players}\n"
        f"Numbers called: {len(called)}\n"
        f"Winners: {len(winners)}",
        parse_mode="Markdown"
    )


async def run_bot():
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN is not set.")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("bingo", bingo)
    )

    application.add_handler(
        CommandHandler("startgame", startgame)
    )

    application.add_handler(
        CommandHandler("stopgame", stopgame)
    )

    application.add_handler(
        CommandHandler("call", call)
    )

    application.add_handler(
        CommandHandler("state", state)
    )

    print("Rudivoller Bingo bot is starting...")

    await application.initialize()
    await application.start()

    if application.updater:
        await application.updater.start_polling()

    print("Rudivoller Bingo bot is ONLINE.")

    while True:
        await asyncio.sleep(3600)


def start_bot_thread():
    thread = threading.Thread(
        target=lambda: asyncio.run(run_bot()),
        daemon=True
    )

    thread.start()

    return thread
