import warnings
import logging

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from gpt import ChatGptService
from util import (
    load_message,
    send_text,
    send_image,
    show_main_menu,
    send_text_buttons,
    load_prompt,
    is_correct_answer,
    dialog_user_info_to_str,
    Dialog,
)
from credentials import CHATGPT_TOKEN, BOT_TOKEN

warnings.filterwarnings("ignore", category=UserWarning)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Стани діалогу
MAIN, RANDOM, GPT, TALK_CHOICE, TALK_CHAT, QUIZ_THEME, QUIZ_ANSWER, TRANSLATE_CHOICE, TRANSLATE_INPUT = range(9)

dialog = Dialog()
chat_gpt = ChatGptService(CHATGPT_TOKEN)


def get_personalities() -> dict:
    """
    Повертає словник доступних особистостей для режиму |Діалог з відомою особистістю|
    """
    return {
        "talk_cobain": "Курт Кобейн",
        "talk_hawking": "Стівен Хокінг",
        "talk_nietzsche": "Фрідріх Ніцше",
        "talk_queen": "Єлизавета II",
        "talk_tolkien": "Джон Толкін",
        "end_btn": "До головного меню",
    }


def get_quiz_themes() -> dict:
    """
    Повертає словник тем для режиму |Квіз|
    """
    return {
        "quiz_prog": "Програмування мовою Python",
        "quiz_math": "Математичні теорії",
        "quiz_biology": "Біологія",
        "end_btn": "До головного меню",
    }


def get_translation_languages() -> dict:
    """
    Повертає словник мов для перекладу.
    """
    return {
        "to_en": "Англійська",
        "to_uk": "Українська",
        "to_cs": "Чеська",
        "to_es": "Іспанська",
        "to_fr": "Французька",
        "end_btn": "До головного меню",
    }


async def answer_callback(update: Update) -> None:
    """
    Безпечно підтверджує callback-запит.
    """
    if update.callback_query:
        await update.callback_query.answer()
        logger.debug("Callback запит підтверджено.")


async def unknown_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE, state: int
) -> int:
    """
    Надсилає повідомлення про введення користувачем невідомої команди і повертає переданий стан.
    """
    logger.info("Невідома команда отримана.")
    await send_text(update, context, "Невідома команда.")
    return state


# === |Початок діалогу з chat-bot / Головне меню| ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Ініціалізує діалог, очищає дані користувача та показує головне меню.
    """
    logger.info("Запуск головного меню.")
    context.user_data.clear()
    text = load_message("main")
    await send_image(update, context, "main")
    await send_text(update, context, text)
    await show_main_menu(
        update,
        context,
        {
            "start": "Головне меню",
            "random": "Дізнатися випадковий факт 🧠",
            "gpt": "Задати питання чату GPT 🤖",
            "talk": "Поговорити з відомою особистістю 👤",
            "quiz": "Взяти участь у квізі ❓",
            "translater": "Перекладач 🌐",
            "cancel": "Завершити діалог з chat-bot",
        },
    )
    return MAIN


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обробляє вибір пункту головного меню.
    """
    query = update.callback_query.data
    logger.info(f"Головне меню: вибрано команду '%s'.", query)
    await answer_callback(update)

    if query == "random":
        return await random_start(update, context)
    elif query == "gpt":
        return await gpt_start(update, context)
    elif query == "talk":
        return await talk_start(update, context)
    elif query == "quiz":
        return await quiz_start(update, context)
    elif query == "translater":
        return await translator_start(update, context)
    else:
        return await unknown_command(update, context, MAIN)


# === Режим |Дізнатись випадковий факт| ===
async def random_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Запускає режим |Дізнатись випадковий факт|
    """
    logger.info("Режим \"Дізнатись випадковий факт\" запущено.")
    text = load_message("random")
    await send_image(update, context, "random")
    await send_text(update, context, text)
    prompt = load_prompt("random")
    content = await chat_gpt.add_message(prompt)
    await send_text_buttons(
        update, context, content, {"more_btn": "Хочу ще факт", "end_btn": "Закінчити"}
    )
    return RANDOM


async def random_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Callback для режиму |Дізнатись випадковий факт|
    """
    query = update.callback_query.data
    logger.info("Режим \"Дізнатись випадковий факт\": callback отримано '%s'.", query)
    await answer_callback(update)
    if query == "more_btn":
        return await random_start(update, context)
    elif query == "end_btn":
        return await start(update, context)
    else:
        return await unknown_command(update, context, RANDOM)


# === Режим |GPT-ЧАТ| ===
async def gpt_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Запускає режим |GPT-чат|
    """
    logger.info("Режим \"GPT-чат\" запущено.")
    context.user_data["mode"] = "gpt"
    dialog.clear_history(update.effective_chat.id)
    prompt = load_prompt("gpt")
    dialog.add_message(update.effective_chat.id, "system", prompt)
    await send_image(update, context, "gpt")
    text = load_message("gpt")
    content = await chat_gpt.send_question(prompt, text)
    await send_text_buttons(update, context, content, {"end_btn": "Закінчити"})
    return GPT


async def gpt_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обробляє текстові повідомлення у режимі |GPT-чату|
    """
    if not update.message or not update.message.text:
        return GPT
    user_message = update.message.text
    logger.info("GPT-чат: отримано повідомлення: %s", user_message)
    dialog.add_message(update.effective_chat.id, "user", user_message)
    try:
        content = await chat_gpt.add_message(user_message)
        logger.debug("GPT-чат: отримано відповідь від моделі.")
        await send_text_buttons(update, context, content, {"end_btn": "Закінчити"})
    except Exception as e:
        logger.error("Помилка в GPT-чат: %s", e)
        await send_text(update, context, f"Сталася помилка: {e}")
    return GPT


async def gpt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Callback для режиму |GPT-чату|
    """
    query = update.callback_query.data
    logger.info("GPT-чат callback: %s", query)
    await answer_callback(update)
    if query == "end_btn":
        return await start(update, context)
    return GPT


# === Режим |Поговорити з відомою особистістю| ===
async def talk_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Запускає режим |Поговорити з відомою особистістю|
    """
    logger.info("Режим \"Поговорити з відомою особистістю\" запущено.")
    context.user_data["mode"] = "talk"
    await send_image(update, context, "talk")
    text = load_message("talk")
    personalities = get_personalities()
    await send_text_buttons(update, context, text, personalities)
    return TALK_CHOICE


async def talk_choice_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Обробляє вибір особистості для діалогу.
    """
    query = update.callback_query.data
    logger.info("Вибір особистості: %s", query)
    await answer_callback(update)
    if query == "end_btn":
        return await start(update, context)
    if query.startswith("talk_"):
        personality_data = {
            "talk_cobain": ("talk_cobain", "Курт Кобейн"),
            "talk_hawking": ("talk_hawking", "Стівен Хокінг"),
            "talk_nietzsche": ("talk_nietzsche", "Фрідріх Ніцше"),
            "talk_queen": ("talk_queen", "Єлизавета II"),
            "talk_tolkien": ("talk_tolkien", "Джон Толкін"),
        }
        if query in personality_data:
            file_name, display_name = personality_data[query]
            logger.info("Обрано особистість: %s", display_name)
            await send_image(update, context, file_name)
            prompt = load_prompt(file_name)
            dialog.clear_history(update.effective_chat.id)
            dialog.add_message(update.effective_chat.id, "system", prompt)
            content = await chat_gpt.send_question(prompt, "")
            await send_text_buttons(
                update,
                context,
                content,
                {"talk": "Інша особистість", "end_btn": "Закінчити"},
            )
            return TALK_CHAT
    return await unknown_command(update, context, TALK_CHOICE)


async def talk_chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обробляє текстові повідомлення у режимі |Поговорити з відомою особистістю|
    """
    if not update.message or not update.message.text:
        return TALK_CHAT
    user_message = update.message.text
    logger.info("\"Поговорити з відомою особистістю\": отримано повідомлення: %s", user_message)
    dialog.add_message(update.effective_chat.id, "user", user_message)
    try:
        content = await chat_gpt.add_message(user_message)
        await send_text_buttons(
            update,
            context,
            content,
            {"talk": "Інша особистість", "end_btn": "Закінчити"},
        )
    except Exception as e:
        logger.error("Помилка в режимі \"Поговорити з відомою особистістю\": %s", e)
        await send_text(update, context, f"Сталася помилка: {e}")
    return TALK_CHAT


async def talk_chat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Callback для режиму |Поговорити з відомою особистістю|
    """
    query = update.callback_query.data
    logger.info("\"Поговорити з відомою особистістю\" callback: %s", query)
    await answer_callback(update)
    if query == "end_btn":
        return await start(update, context)
    elif query == "talk":
        return await talk_start(update, context)
    return TALK_CHAT


# === Режим |Квіз| ===
async def quiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Запускає режим |Квіз|
    """
    logger.info("Режим \"Квіз\" запущено.")
    context.user_data["mode"] = "quiz"
    dialog.clear_history(update.effective_chat.id)
    quiz_themes = get_quiz_themes()
    await send_image(update, context, "quiz")
    text = load_message("quiz")
    await send_text_buttons(update, context, text, quiz_themes)
    return QUIZ_THEME


async def quiz_theme_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Обробляє вибір теми квізу та генерує питання.
    """
    query = update.callback_query.data
    logger.info("Режим \"Квіз\": вибір теми або команда '%s'", query)
    await answer_callback(update)
    quiz_data = {
        "quiz_prog": ("quiz_prog", "Програмування мовою Python"),
        "quiz_math": ("quiz_math", "Математичні теорії"),
        "quiz_biology": ("quiz_biology", "Біологія"),
    }
    if query == "end_btn":
        return await start(update, context)
    elif query == "quiz":
        return await quiz_start(update, context)
    elif query in quiz_data or query == "quiz_more":
        if query in quiz_data:
            # Вибір теми вперше
            file_name, display_name = quiz_data[query]
            context.user_data["theme"] = query
            dialog.clear_history(update.effective_chat.id)
            logger.info("Режим \"Квіз\": обрана тема '%s'", display_name)
        else:
            # При "quiz_more" тема вже збережена
            current_theme = context.user_data.get("theme")
            if not current_theme or current_theme not in quiz_data:
                await send_text(update, context, "Оберіть тему вікторини спочатку.")
                return QUIZ_THEME
            file_name, display_name = quiz_data[current_theme]
            logger.info("Режим \"Квіз\": продовження теми '%s'", display_name)
        await send_image(update, context, file_name)
        base_prompt = load_prompt(file_name)
        dialog.add_message(update.effective_chat.id, "system", base_prompt)
        content = await chat_gpt.send_question(base_prompt, "")
        question_text = content.strip()
        while dialog.has_question_been_asked(update.effective_chat.id, question_text):
            new_q = await chat_gpt.send_question(
                f"Згенеруй нове питання для теми {display_name}", ""
            )
            question_text = new_q.strip()
            logger.debug("Режим \"Квіз\": згенеровано нове питання.")
        dialog.add_quiz_question(update.effective_chat.id, question_text)

        expected_prompt = (
            f"Питання: {question_text}\n"
            "Які відповіді вважаються правильними для цього питання? "
            "Ти повинен мати список можливих правильних відповідей через кому. "
            "Всі відповіді мають бути короткими, не більше 2-х слів."
        )
        chat_gpt.message_list = []
        expected_response = await chat_gpt.send_question(expected_prompt, "")
        expected_answers = [ans.strip().lower() for ans in expected_response.split(",")]
        context.user_data["expected_answers"] = expected_answers
        logger.info("Режим \"Квіз\": збережено очікувані відповіді.")

        await send_text_buttons(
            update,
            context,
            question_text,
            {
                "quiz_more": "Ще питання",
                "quiz": "Обрати іншу тему",
                "end_btn": "Закінчити",
            },
        )
        return QUIZ_ANSWER
    else:
        return await unknown_command(update, context, QUIZ_THEME)


async def quiz_answer_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Обробляє відповідь користувача на поставлене питання квізу від GPT.
    """
    if not update.message or not update.message.text:
        return QUIZ_ANSWER
    user_answer = update.message.text.strip()
    logger.info("Режим \"Квіз\": отримано відповідь '%s'", user_answer)
    if len(user_answer.split()) > 2:
        await send_text(
            update,
            context,
            "Очікується відповідь у вигляді не більше 2-х слів.",
        )
        return QUIZ_ANSWER

    expected_answers = context.user_data.get("expected_answers", [])
    if is_correct_answer(user_answer, expected_answers):
        dialog.increment_correct_answers(update.effective_chat.id)
        correct_count = dialog.get_correct_answers(update.effective_chat.id)
        logger.info("Режим \"Квіз\": відповідь правильна. Поточний лічильник: %d", correct_count)
        await send_text_buttons(
            update,
            context,
            f"Ваша відповідь правильна! 🎉 Кількість правильних відповідей: {correct_count}",
            {
                "quiz_more": "Ще питання",
                "quiz": "Обрати іншу тему",
                "end_btn": "Закінчити",
            },
        )
    else:
        logger.info("Режим \"Квіз\": відповідь неправильна. Очікувані відповіді: %s", expected_answers)
        await send_text_buttons(
            update,
            context,
            f"Неправильно. Правильна відповідь: {', '.join(expected_answers)}",
            {
                "quiz_more": "Ще питання",
                "quiz": "Обрати іншу тему",
                "end_btn": "Закінчити",
            },
        )
    return QUIZ_THEME


# === Режим |Перекладач| ===
async def translator_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Запускає режим /translater (перекладач). Пропонує вибрати мову для перекладу.
    """
    logger.info("Запуск режиму Перекладач.")
    context.user_data["mode"] = "translater"
    await send_image(update, context, "translater")
    text = "Оберіть мову, на яку потрібно перекласти текст:"
    languages = get_translation_languages()
    await send_text_buttons(update, context, text, languages)
    return TRANSLATE_CHOICE


async def translator_choice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обробляє вибір мови для перекладу.
    """
    query = update.callback_query.data
    logger.info("Перекладач: вибір мови '%s'", query)
    await answer_callback(update)
    if query == "end_btn":
        return await start(update, context)
    elif query == "translater":
        return await translator_start(update, context)

    languages = get_translation_languages()
    context.user_data["language_to_cmd"] = query
    context.user_data["language_to"] = languages.get(query, query)

    await send_text(
        update,
        context,
        "Надішліть текст, який потрібно перекласти:"
    )
    return TRANSLATE_INPUT


async def translator_input_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обробляє текстове повідомлення, яке потрібно перекласти, та надсилає переклад.
    """
    if not update.message or not update.message.text:
        return TRANSLATE_INPUT
    original_text = update.message.text.strip()
    logger.info("Перекладач: отримано текст для перекладу: %s", original_text)
    context.user_data["text_to_translate"] = original_text
    context.user_data["language_from"] = "auto"

    # Формується запит до ChatGPT для перекладу
    original_prompt = load_prompt("translater")
    target_language = context.user_data.get("language_to", "Англійська")
    prompt_text = original_prompt.format(target_language=target_language)
    logger.info("Перекладач: формування запиту з prompt: %s", prompt_text)
    translation = await chat_gpt.send_question(prompt_text, original_text)

    # Формуються дані діалогу для відображення
    translation_info = {
        "language_from": context.user_data.get("language_from", "auto"),
        "language_to": target_language,
        "text_to_translate": original_text,
    }
    info_str = dialog_user_info_to_str(translation_info)

    # Надсилається результат перекладу разом з інформацією про параметри
    result_text = f"{translation}\n\n---\n{info_str}"
    await send_text_buttons(
        update,
        context,
        result_text,
        {"translater": "Змінити мову", "end_btn": "Головне меню"},
    )
    return TRANSLATE_CHOICE


# === Фолбек ===
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Примусово завершується діалог з telegram chat-bot при обранні у меню або самостійному введенні команди /cancel.
    """
    logger.info("Діалог завершено командою /cancel.")
    await send_text(update, context, "Діалог завершено.")
    return ConversationHandler.END


conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("start", start),
        CommandHandler("random", random_start),
        CommandHandler("gpt", gpt_start),
        CommandHandler("talk", talk_start),
        CommandHandler("quiz", quiz_start),
        CommandHandler("translater", translator_start),
    ],
    states={
        MAIN: [CallbackQueryHandler(main_menu_callback)],
        RANDOM: [CallbackQueryHandler(random_callback)],
        GPT: [
            MessageHandler(filters.TEXT & (~filters.COMMAND), gpt_message),
            CallbackQueryHandler(gpt_callback),
        ],
        TALK_CHOICE: [CallbackQueryHandler(talk_choice_callback)],
        TALK_CHAT: [
            MessageHandler(filters.TEXT & (~filters.COMMAND), talk_chat_message),
            CallbackQueryHandler(talk_chat_callback),
        ],
        QUIZ_THEME: [CallbackQueryHandler(quiz_theme_callback)],
        QUIZ_ANSWER: [
            MessageHandler(filters.TEXT & (~filters.COMMAND), quiz_answer_handler),
            CallbackQueryHandler(quiz_theme_callback),
        ],
        TRANSLATE_CHOICE: [CallbackQueryHandler(translator_choice_callback)],
        TRANSLATE_INPUT: [MessageHandler(filters.TEXT & (~filters.COMMAND), translator_input_message)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_chat=True,
    allow_reentry=True,
)

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(conv_handler)

logger.info("Чат-бот запущено.")
app.run_polling()
