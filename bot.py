import os
import sys
import asyncio
import subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ["BOT_TOKEN"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👤 Sherlock Bot\n\nОтправь никнейм — найду аккаунты на 300+ сайтах.\n\nПример: john_doe"
    )

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip().lstrip("@")
    if not username or len(username) > 50:
        await update.message.reply_text("❌ Некорректный никнейм.")
        return

    msg = await update.message.reply_text(f"🔍 Ищу {username}...")

    try:
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: subprocess.run(
                [sys.executable, "-m", "sherlock_project", username,
                 "--print-found", "--timeout", "10", "--no-color"],
                capture_output=True, text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )),
            timeout=120
        )

        lines = [l.strip() for l in result.stdout.split("\n") if "[+]" in l]

        if not lines:
            await msg.edit_text(f"😔 Ничего не найдено для {username}")
            return

        text = f"✅ Найдено {len(lines)} аккаунт(ов) для {username}:\n\n"
        for line in lines:
            url = line.replace("[+]", "").strip()
            text += f"• {url}\n"
            if len(text) > 3800:
                await update.message.reply_text(text, disable_web_page_preview=True)
                text = ""

        if text:
            await msg.edit_text(text, disable_web_page_preview=True)

    except asyncio.TimeoutError:
        await msg.edit_text("⏱ Время вышло. Попробуй снова.")
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
    print("Бот запущен...")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
