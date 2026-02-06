import logging
import os
from collections import defaultdict

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from openai import OpenAI

from narrative_prompt import NARRATIVE_PROMPT
from subscription_guard import subscription_guard, check_subs_callback
from telegram.ext import CallbackQueryHandler, CommandHandler

load_dotenv()


TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")

client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
)

user_histories = defaultdict(list)


def ask_gpt(messages):
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Ошибка запроса к GPT: {e}"
    
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await subscription_guard(update, context):
        return

    msg = update.effective_message

    await msg.reply_text(
        "Просто напиши мне привет :)"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await subscription_guard(update, context): return
    user_id = update.effective_user.id
    text = update.message.text

    if not user_histories[user_id]:
        user_histories[user_id].append(
            {"role": "system", "content": NARRATIVE_PROMPT}
        )

    user_histories[user_id].append({"role": "user", "content": text})

    await update.message.chat.send_action(action="typing")

    answer = ask_gpt(user_histories[user_id])

    user_histories[user_id].append({"role": "assistant", "content": answer})

    await update.message.reply_text(answer)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN не найден в .env")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_subs_callback, pattern="check_subs"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен...")
    app.run_polling()
