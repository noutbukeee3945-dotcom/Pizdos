import os
import asyncio
import subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ["BOT_TOKEN"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👤 *Sherlock Bot*\n\n"
        "Отправь мне никнейм — я найду все аккаунты с таким именем в социальных сетях.\n\n"
        "Просто напиши имя пользователя, например: `john_doe`",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Использование:*\n\n"
        "Просто отправь никнейм и я найду аккаунты на сотнях сайтов.\n\n"
        "Команды:\n"
        "/start — начало работы\n"
        "/help — эта справка",
        parse_mode="Markdown"
    )

async def search_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip().lstrip("@")

    if len(username) < 1 or len(username) > 50:
        await update.message.reply_text("❌ Никнейм должен быть от 1 до 50 символов.")
        return

    msg = await update.message.reply_text(
        f"🔍 Ищу `{username}`... Это может занять до 1 минуты.",
        parse_mode="Markdown"
    )

    try:
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    ["sherlock", username, "--print-found", "--timeout", "10", "--no-color"],
                    capture_output=True,
                    text=True
                )
            ),
            timeout=120
        )

        output = result.stdout.strip()
        lines = [l.strip() for l in output.split("\n") if "[+]" in l]

        if not lines:
            await msg.edit_text(
                f"😔 Аккаунты с именем `{username}` не найдены.",
                parse_mode="Markdown"
            )
            return

        found_text = f"✅ *Найдено: {len(lines)} аккаунт(ов)* для `{username}`\n\n"
        chunk = found_text
        for line in lines:
            url = line.replace("[+]", "").strip()
            entry = f"• {url}\n"
            if len(chunk) + len(entry) > 4000:
                await update.message.reply_text(chunk, parse_mode="Markdown", disable_web_page_preview=True)
                chunk = ""
            chunk += entry

        if chunk:
            await msg.edit_text(chunk, parse_mode="Markdown", disable_web_page_preview=True)

    except asyncio.TimeoutError:
        await msg.edit_text("⏱ Превышено время ожидания. Попробуй снова.")
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка: {str(e)}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_username))
    print("Бот запущен...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
