from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes

from gpt import ChatGptService
from util import (
    load_message,
    send_text,
    send_image,
    show_main_menu,
    default_callback_handler,
)

from credentials import CHATGPT_TOKEN, ORGANIZATION, PROJECT_ID, BOT_TOKEN


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = load_message("main")
    await send_image(update, context, "main")
    await send_text(update, context, text)
    await show_main_menu(
        update,
        context,
        {
            "start": "Головне меню",
            "random": "Дізнатися випадковий цікавий факт 🧠",
            "gpt": "Задати питання чату GPT 🤖",
            "talk": "Поговорити з відомою особистістю 👤",
            "quiz": "Взяти участь у квізі ❓",
            # Додати команду в меню можна так:
            # 'command': 'button text'
        },
    )


chat_gpt = ChatGptService(CHATGPT_TOKEN, ORGANIZATION, PROJECT_ID)
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.chat_gpt = chat_gpt

# Зареєструвати обробник команди можна так:
# app.add_handler(CommandHandler('command', handler_func))

# Зареєструвати обробник колбеку можна так:
# app.add_handler(CallbackQueryHandler(app_button, pattern='^app_.*'))
app.add_handler(CallbackQueryHandler(default_callback_handler))
app.run_polling()
