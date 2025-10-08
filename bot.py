import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from openai import AsyncOpenAI

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Системный промпт — строгие правила для 4 класса
SYSTEM_PROMPT = """
Ты — добрый и терпеливый учитель начальной школы в России. Ты помогаешь ученику 4 класса готовиться к ВПР.
Следуй этим правилам:
1. Ученик уже выбрал предмет (русский язык, математика или окружающий мир) — НЕ спрашивай его снова.
2. Если ученик пишет "задачи", "примеры", "правило" и т.п. — сразу давай задание или объяснение ПО ТЕМЕ, которую он уже назвал.
3. В математике: только целые числа, + – × ÷, задачи на движение (путь = скорость × время), периметр, площадь прямоугольника. НЕ используй дроби, уравнения с x, десятичные дроби.
4. В русском: безударные гласные, проверяемые/непроверяемые слова, части речи (существительное, прилагательное, глагол), знаки препинания в конце предложения.
5. В окружающем мире: природные зоны России, строение человека (дыхание, кровообращение), тела и вещества, основные исторические события (Древняя Русь, Иван Грозный, Петр I).
6. Отвечай КОРОТКО: 1–3 предложения. Сразу после вопроса — решение или подсказка.
7. Если не знаешь — скажи: "Это пока не проходят в 4 классе".
8. Никогда не выдумывай факты. Не повторяй одни и те же фразы.
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "Привет! 👋 Я — твой помощник по подготовке к ВПР в 4 классе.\n"
        "Напиши, по какому предмету хочешь позаниматься:\n"
        "• Русский язык\n• Математика\n• Окружающий мир"
    )
    # Сбрасываем историю при старте
    context.user_data["messages"] = []

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех текстовых сообщений с сохранением контекста"""
    user_text = update.message.text

    # Инициализируем историю сообщений, если её нет
    if "messages" not in context.user_data:
        context.user_data["messages"] = []

    messages = context.user_data["messages"]
    messages.append({"role": "user", "content": user_text})

    # Формируем запрос: системный промпт + последние 6 сообщений (3 пары)
    request_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages[-6:]

    try:
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=request_messages,
            max_tokens=250,
            temperature=0.7
        )
        bot_reply = response.choices[0].message.content.strip()
        messages.append({"role": "assistant", "content": bot_reply})
        await update.message.reply_text(bot_reply)
    except Exception as e:
        logging.error(f"Ошибка OpenAI: {e}")
        await update.message.reply_text("Ой! 😕 Не получилось ответить. Попробуй написать ещё раз!")

def main():
    """Основная функция запуска бота"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("❌ Не задан TELEGRAM_BOT_TOKEN в файле .env")
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("❌ Не задан OPENAI_API_KEY в файле .env")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Бот запущен! Напиши ему в Telegram.")
    app.run_polling()

if __name__ == "__main__":
    main()