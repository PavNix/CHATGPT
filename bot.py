from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    ContextTypes,
    CommandHandler,
)

from gpt import ChatGptService
from util import (
    load_message,
    send_text,
    send_image,
    show_main_menu,
    callback_echo_handler,
    load_prompt,
    send_text_buttons,
)

from credentials import CHATGPT_TOKEN, BOT_TOKEN, ORGANIZATION, PROJECT_ID


async def button_logic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    query = update.callback_query.data

    if query == "more_btn":
        await random(update, context)
    if query == "end_btn":
        await start(update, context)


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


async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = load_message("random")
    await send_image(update, context, "random")
    await send_text(update, context, text)
    prompt = load_prompt("random")
    content = await chat_gpt.add_message(prompt)

    await send_text_buttons(
        update, context, content, {"more_btn": "Хочу ще факт", "end_btn": "Закінчити"}
    )


chat_gpt = ChatGptService(CHATGPT_TOKEN, ORGANIZATION, PROJECT_ID)
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.chat_gpt = chat_gpt

# Зареєструвати обробник команди можна так:
# app.add_handler(CommandHandler('command', handler_func))
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("random", random))

# Зареєструвати обробник колбеку можна так:
# app.add_handler(CallbackQueryHandler(app_button, pattern='^app_.*'))
app.add_handler(
    CallbackQueryHandler(button_logic_handler, pattern="^(more_btn|end_btn)$")
)
app.add_handler(CallbackQueryHandler(callback_echo_handler, pattern=".*"))

app.run_polling()
