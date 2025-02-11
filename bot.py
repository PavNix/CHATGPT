from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
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
    Dialog,
)

from credentials import CHATGPT_TOKEN, BOT_TOKEN, ORGANIZATION, PROJECT_ID

dialog = Dialog()


def get_personalities():
    return {
        "talk_cobain": "Курт Кобейн",
        "talk_hawking": "Стівен Хокінг",
        "talk_nietzsche": "Фрідріх Ніцше",
        "talk_queen": "Єлизавета II",
        "talk_tolkien": "Джон Толкін",
        "end_btn": "До головного меню",
    }


async def button_logic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    query = update.callback_query.data

    if query == "more_btn":
        await random(update, context)
    elif query == "end_btn":
        await start(update, context)
    elif query == "talk":
        personalities = get_personalities()

        await send_image(update, context, "talk")
        text = load_message("talk")
        await send_text_buttons(update, context, text, personalities)

        clear_active_handlers(context)
        handler = CallbackQueryHandler(callback_talk_personality, pattern="^talk.*$")
        app.add_handler(handler)
        context.user_data["active_handler"] = handler
        return


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (
        not update.message
        or not update.message.text
        or update.message.text.startswith("/")
    ):
        return

    chat_id = update.effective_chat.id
    user_message = update.message.text

    mode = context.user_data.get("mode", None)

    if mode == "gpt":
        dialog.add_message(chat_id, "user", user_message)

        try:
            content = await chat_gpt.add_message(user_message)
            await send_text_buttons(update, context, content, {"end_btn": "Закінчити"})
        except Exception as e:
            await send_text(update, context, f"Сталася помилка: {e}")

    elif mode == "talk":
        dialog.add_message(chat_id, "user", user_message)

        try:
            content = await chat_gpt.add_message(user_message)
            await send_text_buttons(
                update,
                context,
                content,
                {"end_btn": "Закінчити", "talk": "Інша особистість"},
            )
        except Exception as e:
            await send_text(update, context, f"Сталася помилка: {e}")

    elif mode == "quiz":
        await send_text(
            update,
            context,
            f"Режим 'quiz' пока не реализован. Вы написали: {user_message}",
        )


def clear_active_handlers(context):
    if "active_handler" in context.user_data:
        app.remove_handler(context.user_data["active_handler"])
        del context.user_data["active_handler"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_active_handlers(context)
    context.user_data.clear()

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


async def gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if context.user_data.get("mode") == "gpt":
            return

        context.user_data["mode"] = "gpt"
        clear_active_handlers(context)

        universal_handler = MessageHandler(
            filters.TEXT & (~filters.COMMAND), message_handler
        )
        app.add_handler(universal_handler)
        context.user_data["active_handler"] = universal_handler

        text = load_message("gpt")
        await send_image(update, context, "gpt")
        prompt = load_prompt("gpt")
        dialog.clear_history(update.effective_chat.id)
        dialog.add_message(update.effective_chat.id, "system", prompt)
        content = await chat_gpt.send_question(prompt, text)
        await send_text_buttons(update, context, content, {"end_btn": "Закінчити"})
    except Exception as e:
        await send_text(update, context, f"Сталася помилка: {e}")


async def talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if context.user_data.get("mode") == "talk":
            return

        context.user_data["mode"] = "talk"
        clear_active_handlers(context)

        personalities = get_personalities()

        await send_image(update, context, "talk")
        text = load_message("talk")
        await send_text_buttons(update, context, text, personalities)

        handler = CallbackQueryHandler(callback_talk_personality, pattern="^talk_.*$")
        app.add_handler(handler)
        context.user_data["active_handler"] = handler

    except Exception as e:
        await send_text(update, context, f"Сталася помилка: {e}")


async def callback_talk_personality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.callback_query.answer()
        query = update.callback_query.data

        personality_data = {
            "talk_cobain": ("talk_cobain", "Курт Кобейн"),
            "talk_hawking": ("talk_hawking", "Стівен Хокінг"),
            "talk_nietzsche": ("talk_nietzsche", "Фрідріх Ніцше"),
            "talk_queen": ("talk_queen", "Єлизавета II"),
            "talk_tolkien": ("talk_tolkien", "Джон Толкін"),
        }

        if query in personality_data:
            file_name, display_name = personality_data[query]

            await send_image(update, context, file_name)
            prompt = load_prompt(file_name)
            dialog.clear_history(update.effective_chat.id)
            dialog.add_message(update.effective_chat.id, "system", prompt)

            content = await chat_gpt.send_question(prompt, "")
            await send_text_buttons(
                update,
                context,
                f"Ви обрали {display_name}: {content}",
                {"end_btn": "Закінчити", "talk": "Інша особистість"},
            )

            universal_handler = MessageHandler(
                filters.TEXT & (~filters.COMMAND), message_handler
            )
            app.add_handler(universal_handler)
            context.user_data["active_handler"] = universal_handler
    except Exception as e:
        await send_text(update, context, f"Сталася помилка: {e}")


chat_gpt = ChatGptService(CHATGPT_TOKEN, ORGANIZATION, PROJECT_ID)
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.chat_gpt = chat_gpt

# Зареєструвати обробник команди можна так:
# app.add_handler(CommandHandler('command', handler_func))
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("random", random))
app.add_handler(CommandHandler("gpt", gpt))
app.add_handler(CommandHandler("talk", talk))


# Зареєструвати обробник колбеку можна так:
# app.add_handler(CallbackQueryHandler(app_button, pattern='^app_.*'))
app.add_handler(
    CallbackQueryHandler(button_logic_handler, pattern="^(more_btn|end_btn|talk)$")
)
app.add_handler(CallbackQueryHandler(callback_talk_personality, pattern="^talk_.*$"))

app.add_handler(CallbackQueryHandler(callback_echo_handler, pattern=".*"))

app.run_polling()
