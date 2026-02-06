from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import Forbidden, BadRequest


REQUIRED_CHANNELS = [
    (-1003808440892, "https://t.me/nikitakuvsh_developer", "Моя разработка"),
    (-1001804460457, "https://t.me/frankl_logotherapy", "Человек в поисках смысла"),
]


def _subscribe_keyboard():
    buttons = [
        [InlineKeyboardButton(f"Подписаться: {title}", url=url)]
        for _, url, title in REQUIRED_CHANNELS
    ]

    buttons.append(
        [InlineKeyboardButton("Проверить подписку", callback_data="check_subs")]
    )

    return InlineKeyboardMarkup(buttons)


async def subscription_guard(update, context) -> bool:
    user_id = update.effective_user.id
    msg = update.effective_message

    for chat_id, _, _ in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id, user_id)
            if member.status in ["left", "kicked"]:
                await msg.reply_text(
                    "Чтобы пользоваться ботом, подпишитесь на каналы 👇",
                    reply_markup=_subscribe_keyboard(),
                )
                return False
        except Forbidden:
            return False

    return True

async def check_subs_callback(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    not_subscribed = []

    for chat_id, url, title in REQUIRED_CHANNELS:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status in ["left", "kicked"]:
            not_subscribed.append((url, title))

    if not_subscribed:
        buttons = [
            [InlineKeyboardButton(f"Подписаться: {title}", url=url)]
            for url, title in not_subscribed
        ]
        buttons.append(
            [InlineKeyboardButton("Проверить подписку", callback_data="check_subs")]
        )

        try:
            await query.edit_message_text(
                "❌ Вы подписаны не на все каналы.\nПодпишитесь и нажмите проверить ещё раз 👇",
                reply_markup=InlineKeyboardMarkup(buttons),
            )
        except BadRequest as e:
            if "Message is not modified" in str(e):
                await query.answer("Вы всё ещё не подписаны 😉", show_alert=True)
            else:
                raise
        return

    await query.edit_message_text(
        "✅ Подписка подтверждена! Теперь можно пользоваться ботом. Просто напиши Привет :)"
    )