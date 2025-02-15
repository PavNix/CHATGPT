from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    BotCommand,
    MenuButtonCommands,
    BotCommandScopeChat,
    MenuButtonDefault,
)
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from typing import Dict, Any, List

import logging

logger = logging.getLogger(__name__)

def dialog_user_info_to_str(user_data: Dict[str, Any]) -> str:
    """
    Конвертує обʼєкт user_data у рядок з відображенням ключів на основі мапінгу.

    Параметри:
        user_data (Dict[str, Any]): Словник з даними користувача.
    Повертає:
        str: Строкове представлення даних користувача.
    """
    mapper = {
        "language_from": "Мова оригіналу",
        "language_to": "Мова перекладу",
        "text_to_translate": "Текст для перекладу",
    }
    result = "\n".join(f"{mapper.get(k, k)}: {v}" for k, v in user_data.items())
    logger.debug("dialog_user_info_to_str: %s", result)
    return result


async def send_text(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
) -> Message:
    """
    Надсилає текстове повідомлення з Markdown-розміткою до чату.
    Якщо рядок невалідний для Markdown (непарне число символів '_'), надсилає попередження.

    Параметри:
        update (Update): Оновлення Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст.
        text (str): Текстове повідомлення.
    Повертає:
        Message: Надіслане повідомлення.
    """
    if text.count("_") % 2 != 0:
        warning_message = (
            f"Рядок '{text}' є невалідним для Markdown. "
            "Скористуйтесь методом send_html()"
        )
        print(warning_message)
        logger.warning(warning_message)
        return await update.message.reply_text(warning_message)

    text = text.encode("utf16", errors="surrogatepass").decode("utf16")
    logger.debug("send_text: %s", text)
    return await context.bot.send_message(
        chat_id=update.effective_chat.id, text=text, parse_mode=ParseMode.MARKDOWN
    )


async def send_html(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
) -> Message:
    """
    Надсилає текстове повідомлення з HTML-розміткою до чату.

    Параметри:
        update (Update): Оновлення Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст.
        text (str): Текстове повідомлення.
    Повертає:
        Message: Надіслане повідомлення.
    """
    text = text.encode("utf16", errors="surrogatepass").decode("utf16")
    logger.debug("send_html: %s", text)
    return await context.bot.send_message(
        chat_id=update.effective_chat.id, text=text, parse_mode=ParseMode.HTML
    )


async def send_text_buttons(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, buttons: Dict[str, str]
) -> Message:
    """
    Надсилає текстове повідомлення з кнопками.

    Параметри:
        update (Update): Оновлення Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст.
        text (str): Текстове повідомлення.
        buttons (Dict[str, str]): Словник, де ключ – callback_data, значення – текст кнопки.
    Повертає:
        Message: Надіслане повідомлення.
    """
    text = text.encode("utf16", errors="surrogatepass").decode("utf16")
    keyboard: List[List[InlineKeyboardButton]] = []
    for key, value in buttons.items():
        button = InlineKeyboardButton(str(value), callback_data=str(key))
        keyboard.append([button])
    reply_markup = InlineKeyboardMarkup(keyboard)
    logger.debug("send_text_buttons: кнопки %s", buttons)
    return await context.bot.send_message(
        update.effective_message.chat_id,
        text=text,
        reply_markup=reply_markup,
        message_thread_id=update.effective_message.message_thread_id,
    )


async def send_image(
    update: Update, context: ContextTypes.DEFAULT_TYPE, name: str
) -> Message:
    """
    Надсилає зображення з папки resources/images.

    Параметри:
        update (Update): Оновлення Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст.
        name (str): Назва файлу зображення (без розширення).
    Повертає:
        Message: Надіслане повідомлення з фото.
    """
    logger.debug("send_image: завантаження зображення %s", name)
    with open(f"resources/images/{name}.jpg", "rb") as image:
        return await context.bot.send_photo(
            chat_id=update.effective_chat.id, photo=image
        )


async def show_main_menu(
    update: Update, context: ContextTypes.DEFAULT_TYPE, commands: Dict[str, str]
) -> None:
    """
    Встановлює команди бота та відображає головне меню.

    Параметри:
        update (Update): Оновлення Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст.
        commands (Dict[str, str]): Словник команд (ключ – команда, значення – опис).
    """
    command_list = [BotCommand(key, value) for key, value in commands.items()]
    await context.bot.set_my_commands(
        command_list, scope=BotCommandScopeChat(chat_id=update.effective_chat.id)
    )
    await context.bot.set_chat_menu_button(
        menu_button=MenuButtonCommands(), chat_id=update.effective_chat.id
    )
    logger.info("Головне меню встановлено.")


async def hide_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Видаляє команди бота та скидає меню.

    Параметри:
        update (Update): Оновлення Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст.
    """
    await context.bot.delete_my_commands(
        scope=BotCommandScopeChat(chat_id=update.effective_chat.id)
    )
    await context.bot.set_chat_menu_button(
        menu_button=MenuButtonDefault(), chat_id=update.effective_chat.id
    )
    logger.info("Головне меню сховано.")


def load_message(name: str) -> str:
    """
    Завантажує текст повідомлення з файлу у папці resources/messages.

    Параметри:
        name (str): Ім'я файлу (без розширення).
    Повертає:
        str: Вміст файлу.
    """
    try:
        with open(f"resources/messages/{name}.txt", "r", encoding="utf8") as file:
            content = file.read()
            logger.debug("load_message: %s", name)
            return content
    except Exception as e:
        logger.error("Помилка завантаження повідомлення %s: %s", name, e)
        return ""


def load_prompt(name: str) -> str:
    """
    Завантажує prompt із файлу в папці resources/prompts.

    Параметри:
        name (str): Ім'я файлу (без розширення).
    Повертає:
        str: Вміст файлу.
    """
    try:
        with open(f"resources/prompts/{name}.txt", "r", encoding="utf8") as file:
            content = file.read()
            logger.debug("load_prompt: %s", name)
            return content
    except Exception as e:
        logger.error("Помилка завантаження prompt %s: %s", name, e)
        return ""


async def callback_echo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Простий callback-обробник, який відповідає з підтвердженням натискання кнопки.

    Параметри:
        update (Update): Оновлення Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст.
    """
    await update.callback_query.answer()
    query = update.callback_query.data
    logger.info("callback_echo_handler: кнопка %s", query)
    await send_html(update, context, f"Ви натиснули на кнопку {query}")


def normalize_answer(text: str) -> str:
    """
    Нормалізує відповідь, приводячи її до нижнього регістру, видаляючи задані символи пунктуації та зайві прогалини.

    Параметри:
        text (str): Початковий текст.
    Повертає:
        str: Нормалізований текст.
    """
    text = text.lower()
    remove_chars = "()[]{}.,!"
    for ch in remove_chars:
        text = text.replace(ch, "")
    text = text.strip()
    while "  " in text:
        text = text.replace("  ", " ")
    return text


def is_correct_answer(user_answer: str, answers_list: List[str]) -> bool:
    """
    Перевіряє, чи є відповідь користувача коректною, порівнюючи з очікуваними відповідями.

    Параметри:
        user_answer (str): Відповідь користувача.
        answers_list (List[str]): Список очікуваних відповідей.
    Повертає:
        bool: True, якщо відповідь коректна, інакше False.
    """
    user_norm = normalize_answer(user_answer)
    for ans in answers_list:
        ans_norm = normalize_answer(ans)
        if user_norm == ans_norm:
            return True
        if user_norm in ans_norm or ans_norm in user_norm:
            return True
    return False


class Dialog:
    """
    Клас для управління історією діалогу та квізів.
    """
    def __init__(self) -> None:
        """
        Ініціалізує історію діалогів, історію квізів та лічильники правильних відповідей.
        """
        self.dialogs: Dict[int, List[Dict[str, str]]] = {}
        self.quiz_history: Dict[int, List[str]] = {}
        self.correct_answers: Dict[int, int] = {}
        logger.info("Ініціалізовано Dialog.")

    def get_history(self, chat_id: int) -> List[Dict[str, str]]:
        """
        Отримує історію повідомлень для вказаного чату.

        Параметри:
            chat_id (int): Ідентифікатор чату.
        Повертає:
            List[Dict[str, str]]: Список повідомлень діалогу.
        """
        return self.dialogs.get(chat_id, [])

    def add_message(self, chat_id: int, role: str, content: str) -> None:
        """
        Додає повідомлення до історії діалогу.

        Параметри:
            chat_id (int): Ідентифікатор чату.
            role (str): Роль відправника (наприклад, "user" або "system").
            content (str): Текст повідомлення.
        """
        if chat_id not in self.dialogs:
            self.dialogs[chat_id] = []
        self.dialogs[chat_id].append({"role": role, "content": content})
        logger.debug("Додано повідомлення для чату %d: %s", chat_id, content)

    def clear_history(self, chat_id: int) -> None:
        """
        Очищає історію діалогу та квізів для вказаного чату.

        Параметри:
            chat_id (int): Ідентифікатор чату.
        """
        if chat_id in self.dialogs:
            del self.dialogs[chat_id]
        if chat_id in self.quiz_history:
            del self.quiz_history[chat_id]
        if chat_id in self.correct_answers:
            del self.correct_answers[chat_id]
        logger.info("Історія для чату %d очищена.", chat_id)

    def add_quiz_question(self, chat_id: int, question: str) -> None:
        """
        Додає квізове питання до історії для зазначеного чату.

        Параметри:
            chat_id (int): Ідентифікатор чату.
            question (str): Текст питання.
        """
        if chat_id not in self.quiz_history:
            self.quiz_history[chat_id] = []
        self.quiz_history[chat_id].append(question)
        logger.debug("Додано квізове питання для чату %d: %s", chat_id, question)

    def has_question_been_asked(self, chat_id: int, question: str) -> bool:
        """
        Перевіряє, чи було задано це питання раніше у квізі.

        Параметри:
            chat_id (int): Ідентифікатор чату.
            question (str): Текст питання.
        Повертає:
            bool: True, якщо питання вже було поставлено, інакше False.
        """
        return chat_id in self.quiz_history and question in self.quiz_history[chat_id]

    def increment_correct_answers(self, chat_id: int) -> None:
        """
        Збільшує лічильник правильних відповідей для вказаного чату.

        Параметри:
            chat_id (int): Ідентифікатор чату.
        """
        if chat_id not in self.correct_answers:
            self.correct_answers[chat_id] = 0
        self.correct_answers[chat_id] += 1
        logger.debug("Чат %d: правильних відповідей %d", chat_id, self.correct_answers[chat_id])

    def get_correct_answers(self, chat_id: int) -> int:
        """
        Отримує кількість правильних відповідей для цього чату.

        Параметри:
            chat_id (int): Ідентифікатор чату.
        Повертає:
            int: Кількість правильних відповідей.
        """
        return self.correct_answers.get(chat_id, 0)
