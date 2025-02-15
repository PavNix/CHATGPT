from openai import OpenAI
import httpx
import logging

logger = logging.getLogger(__name__)

class ChatGptService:
    """
    Сервіс для спілкування з ChatGPT через OpenAI API.
    """

    client: OpenAI = None
    message_list: list = None

    def __init__(self, token):
        """
        Ініціалізує клієнта OpenAI та очищує історію повідомлень.

        Параметри:
            token (str): API-ключ. Якщо починається з "gpt:", перетворюється.
        """

        token = "sk-proj-" + token[:3:-1] if token.startswith("gpt:") else token
        logger.info("Ініціалізація ChatGptService з токеном %s", token[:10] + "...")
        self.client = OpenAI(
            http_client=httpx.Client(proxy="http://18.199.183.77:49232"),
            api_key=token,
        )
        self.message_list = []


    async def send_message_list(self) -> str:
        """
        Надсилає список повідомлень у модель та повертає відповідь.

        Повертає:
           str: Зміст відповіді моделі.
        """
        try:
            logger.debug("Відправка повідомлень: %s", self.message_list)
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=self.message_list,
                max_tokens=3000,
                temperature=0.9,
            )
            message = completion.choices[0].message
            self.message_list.append(message)
            logger.info("Отримано відповідь від ChatGPT.")
            return message.content
        except Exception as e:
            logger.error("Помилка відправки повідомлень: %s", e)
            return f"Помилка під час виконання: {e}"

    def set_prompt(self, prompt_text: str) -> None:
        """
        Встановлює системний prompt, очищуючи історію повідомлень.

        Параметри:
            prompt_text (str): Текст prompt(у).
        """
        logger.info("Встановлення prompt: %s", prompt_text)
        self.message_list.clear()
        self.message_list.append({"role": "system", "content": prompt_text})

    async def add_message(self, message_text: str) -> str:
        """
        Додає повідомлення користувача до історії та надсилає запит.

        Параметри:
            message_text (str): Повідомлення користувача.
        Повертає:
            str: Відповідь моделі.
        """
        logger.info("Додається повідомлення користувача: %s", message_text)
        self.message_list.append({"role": "user", "content": message_text})
        return await self.send_message_list()

    async def send_question(self, prompt_text: str, message_text: str) -> str:
        """
        Очищає історію повідомлень, встановлює системний prompt та надсилає повідомлення користувача.

        Параметри:
            prompt_text (str): Текст системного prompt.
            message_text (str): Повідомлення користувача.
        Повертає:
            str: Відповідь моделі.
        """
        logger.info("Надсилання запиту з prompt: %s", prompt_text)
        self.message_list.clear()
        self.message_list.append({"role": "system", "content": prompt_text})
        self.message_list.append({"role": "user", "content": message_text})
        return await self.send_message_list()
