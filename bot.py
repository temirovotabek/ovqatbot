# -*- coding: utf-8 -*-
"""
Телеграм-бот "Что приготовить?" — двуязычный (ru/uz) кулинарный помощник
с учётом узбекского базара, семейных предпочтений и списка покупок.

Запуск локально:
    pip install -r requirements.txt
    cp .env.example .env   # и заполнить токены
    python bot.py

Деплой на Railway: см. README.md
"""
import logging
import os

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import ai_client
import storage
from texts import t

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Клавиатуры
# ---------------------------------------------------------------------------

def lang_kb():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🇷🇺 Русский", callback_data="lang:ru"),
          InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang:uz")]]
    )


def main_menu_kb(lang):
    rows = [
        [InlineKeyboardButton(t(lang, "btn_ingredients"), callback_data="menu:ingredients")],
        [InlineKeyboardButton(t(lang, "btn_quick"), callback_data="menu:quick"),
         InlineKeyboardButton(t(lang, "btn_byproduct"), callback_data="menu:byproduct")],
        [InlineKeyboardButton(t(lang, "btn_surprise"), callback_data="menu:surprise"),
         InlineKeyboardButton(t(lang, "btn_missing"), callback_data="menu:missing")],
        [InlineKeyboardButton(t(lang, "btn_people"), callback_data="menu:people"),
         InlineKeyboardButton(t(lang, "btn_mood"), callback_data="menu:mood")],
        [InlineKeyboardButton(t(lang, "btn_budget"), callback_data="menu:budget"),
         InlineKeyboardButton(t(lang, "btn_weekmenu"), callback_data="menu:weekmenu")],
        [InlineKeyboardButton(t(lang, "btn_favorites"), callback_data="menu:favorites"),
         InlineKeyboardButton(t(lang, "btn_shoplist"), callback_data="menu:shoplist")],
        [InlineKeyboardButton(t(lang, "btn_settings"), callback_data="menu:settings")],
    ]
    return InlineKeyboardMarkup(rows)


def back_kb(lang):
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(t(lang, "back_to_menu"), callback_data="menu:main")]]
    )


def choices_kb(lang, pairs, back=True):
    """pairs: список (text_key, callback_data)"""
    rows = [[InlineKeyboardButton(t(lang, key), callback_data=cb)] for key, cb in pairs]
    if back:
        rows.append([InlineKeyboardButton(t(lang, "back_to_menu"), callback_data="menu:main")])
    return InlineKeyboardMarkup(rows)


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def build_user_ctx(user_id: int) -> dict:
    user = storage.get_user(user_id)
    return {
        "family_size": user["family_size"],
        "allergies": user["allergies"],
        "dislikes": user["dislikes"],
        "favorites": storage.list_favorites(user_id),
        "recent_history": storage.recent_history(user_id),
    }


async def generate_and_send(update_or_query, context, lang, user_id, prompt, edit=False, image_bytes=None):
    user_ctx = build_user_ctx(user_id)
    chat = update_or_query.effective_chat if hasattr(update_or_query, "effective_chat") else None

    if edit:
        msg = await update_or_query.edit_message_text(t(lang, "generating"))
    else:
        msg = await context.bot.send_message(chat_id=chat.id, text=t(lang, "generating"))

    try:
        text, titles = ai_client.ask(lang, user_ctx, prompt, image_bytes=image_bytes)
    except Exception as e:
        logger.exception("Ошибка Gemini API")
        await msg.edit_text(f"⚠️ {e}")
        return

    if titles:
        storage.add_history(user_id, titles)

    await msg.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_kb(lang))


async def download_photo_bytes(update: Update) -> bytes:
    photo = update.message.photo[-1]  # самое большое разрешение
    tg_file = await photo.get_file()
    return bytes(await tg_file.download_as_bytearray())


async def process_missing_ingredients(reply_target, context, lang, user_id, prompt, image_bytes=None):
    """Общая логика сценария 'не хватает ингредиентов' — работает и с текстом, и с фото."""
    full_prompt = (
        prompt + " Предложи, что из этого можно приготовить, "
        "и отдельным списком укажи, каких ключевых продуктов не хватает "
        "(в конце ответа добавь строку 'НЕДОСТАЁТ: продукт1, продукт2, ...')."
    )
    user_ctx = build_user_ctx(user_id)
    msg = await reply_target.reply_text(t(lang, "generating"))
    try:
        resp_text, titles = ai_client.ask(lang, user_ctx, full_prompt, image_bytes=image_bytes)
    except Exception as e:
        logger.exception("Ошибка Gemini API")
        await msg.edit_text("⚠️ " + str(e))
        return
    missing_items = []
    if "НЕДОСТАЁТ:" in resp_text:
        main_part, missing_part = resp_text.split("НЕДОСТАЁТ:", 1)
        missing_items = [x.strip() for x in missing_part.replace("\n", ",").split(",") if x.strip()]
        resp_text = main_part.strip()
    if titles:
        storage.add_history(user_id, titles)
    context.user_data["pending_missing_items"] = missing_items
    rows = []
    if missing_items:
        rows.append([InlineKeyboardButton(t(lang, "btn_add_to_shoplist"), callback_data="shop:addmissing")])
    rows.append([InlineKeyboardButton(t(lang, "back_to_menu"), callback_data="menu:main")])
    await msg.edit_text(resp_text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(rows))


def get_lang(user_id: int) -> str:
    return storage.get_user(user_id)["language"]


# ---------------------------------------------------------------------------
# Команды
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if storage.has_user(user_id):
        lang = get_lang(user_id)
        await update.message.reply_text(t(lang, "main_menu_title"), reply_markup=main_menu_kb(lang))
    else:
        storage.get_user(user_id)  # создать запись с языком по умолчанию
        await update.message.reply_text(t("ru", "choose_lang"), reply_markup=lang_kb())


# ---------------------------------------------------------------------------
# Обработка нажатий на кнопки
# ---------------------------------------------------------------------------

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    data = query.data
    context.user_data["awaiting"] = None

    # --- выбор языка ---
    if data.startswith("lang:"):
        lang = data.split(":")[1]
        storage.set_language(user_id, lang)
        await query.edit_message_text(t(lang, "lang_set"))
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=t(lang, "main_menu_title"),
            reply_markup=main_menu_kb(lang),
        )
        return

    lang = get_lang(user_id)

    # --- главное меню ---
    if data == "menu:main":
        await query.edit_message_text(t(lang, "main_menu_title"), reply_markup=main_menu_kb(lang))
        return

    if data == "menu:ingredients":
        context.user_data["awaiting"] = "ingredients"
        await query.edit_message_text(t(lang, "ask_ingredients"), reply_markup=back_kb(lang))
        return

    if data == "menu:quick":
        await query.edit_message_text(
            t(lang, "ask_time"),
            reply_markup=choices_kb(lang, [
                ("time_15", "time:15"), ("time_30", "time:30"),
                ("time_60", "time:60"), ("time_any", "time:any"),
            ]),
        )
        return

    if data.startswith("time:"):
        minutes = data.split(":")[1]
        label = {"15": "15 минут", "30": "30 минут", "60": "1 час", "any": "любое время"}[minutes]
        prompt = f"Предложи рецепты, которые готовятся за {label}. Учитывай размер семьи: {build_user_ctx(user_id)['family_size']} человек."
        await generate_and_send(query, context, lang, user_id, prompt, edit=True)
        return

    if data == "menu:byproduct":
        await query.edit_message_text(
            t(lang, "ask_product"),
            reply_markup=choices_kb(lang, [
                ("product_chicken", "product:chicken"), ("product_beef", "product:beef"),
                ("product_fish", "product:fish"), ("product_potato", "product:potato"),
                ("product_veg", "product:veg"), ("product_pasta", "product:pasta"),
                ("product_other", "product:other"),
            ]),
        )
        return

    if data.startswith("product:"):
        product = data.split(":")[1]
        if product == "other":
            context.user_data["awaiting"] = "product_other"
            await query.edit_message_text(t(lang, "ask_product_other"), reply_markup=back_kb(lang))
            return
        names = {
            "chicken": "курица", "beef": "говядина", "fish": "рыба",
            "potato": "картофель", "veg": "овощи", "pasta": "макароны",
        }
        prompt = f"Предложи рецепты, где основной продукт — {names[product]}."
        await generate_and_send(query, context, lang, user_id, prompt, edit=True)
        return

    if data == "menu:surprise":
        prompt = "Удиви меня — предложи одно случайное интересное блюдо для сегодняшнего ужина."
        await generate_and_send(query, context, lang, user_id, prompt, edit=True)
        return

    if data == "menu:missing":
        context.user_data["awaiting"] = "missing_have"
        await query.edit_message_text(t(lang, "ask_missing_have"), reply_markup=back_kb(lang))
        return

    if data == "menu:people":
        await query.edit_message_text(
            t(lang, "ask_people"),
            reply_markup=choices_kb(lang, [
                ("people_2", "people:2"), ("people_3", "people:3"),
                ("people_4", "people:4"), ("people_6", "people:6"),
                ("people_other", "people:other"),
            ]),
        )
        return

    if data.startswith("people:"):
        val = data.split(":")[1]
        if val == "other":
            context.user_data["awaiting"] = "people_other"
            await query.edit_message_text(t(lang, "ask_people_other"), reply_markup=back_kb(lang))
            return
        context.user_data["awaiting"] = "people_dish"
        context.user_data["people_n"] = val
        await query.edit_message_text(t(lang, "ask_people_dish", n=val), reply_markup=back_kb(lang))
        return

    if data == "menu:mood":
        await query.edit_message_text(
            t(lang, "ask_mood"),
            reply_markup=choices_kb(lang, [
                ("mood_light", "mood:light"), ("mood_hearty", "mood:hearty"),
                ("mood_healthy", "mood:healthy"), ("mood_spicy", "mood:spicy"),
                ("mood_sweet", "mood:sweet"),
            ]),
        )
        return

    if data.startswith("mood:"):
        mood = data.split(":")[1]
        names = {
            "light": "лёгкое", "hearty": "сытное", "healthy": "полезное",
            "spicy": "острое", "sweet": "сладкое",
        }
        prompt = f"Предложи блюда в категории «{names[mood]}»."
        await generate_and_send(query, context, lang, user_id, prompt, edit=True)
        return

    if data == "menu:budget":
        await query.edit_message_text(
            t(lang, "ask_budget"),
            reply_markup=choices_kb(lang, [
                ("budget_50k", "budget:50000"), ("budget_100k", "budget:100000"),
                ("budget_200k", "budget:200000"), ("budget_other", "budget:other"),
            ]),
        )
        return

    if data.startswith("budget:"):
        val = data.split(":")[1]
        if val == "other":
            context.user_data["awaiting"] = "budget_other"
            await query.edit_message_text(t(lang, "ask_budget_other"), reply_markup=back_kb(lang))
            return
        prompt = f"Бюджет на сегодняшний ужин — примерно {val} сум. Предложи блюда, в которые можно уложиться на ташкентском базаре."
        await generate_and_send(query, context, lang, user_id, prompt, edit=True)
        return

    if data == "menu:weekmenu":
        fam = build_user_ctx(user_id)["family_size"]
        prompt = f"Составь меню на неделю (завтрак/обед/ужин на каждый день) для семьи из {fam} человек и в конце дай общий список покупок одним списком."
        await generate_and_send(query, context, lang, user_id, prompt, edit=True)
        return

    # --- любимые блюда ---
    if data == "menu:favorites":
        await show_favorites(query, lang, user_id, edit=True)
        return

    if data == "fav:add":
        context.user_data["awaiting"] = "fav_add"
        await query.edit_message_text(t(lang, "ask_add_favorite"), reply_markup=back_kb(lang))
        return

    if data.startswith("fav:remove:"):
        fav_id = int(data.split(":")[2])
        storage.remove_favorite(fav_id)
        await query.answer(t(lang, "favorite_removed"))
        await show_favorites(query, lang, user_id, edit=True)
        return

    # --- список покупок ---
    if data == "menu:shoplist":
        await show_shoplist(query, lang, user_id, edit=True)
        return

    if data == "shop:add":
        context.user_data["awaiting"] = "shop_add"
        await query.edit_message_text(t(lang, "ask_add_shoplist"), reply_markup=back_kb(lang))
        return

    if data == "shop:clear":
        storage.clear_shopping_list(user_id)
        await query.answer(t(lang, "shoplist_cleared"))
        await show_shoplist(query, lang, user_id, edit=True)
        return

    # --- настройки ---
    if data == "menu:settings":
        await show_settings(query, lang, user_id, edit=True)
        return

    if data == "set:lang":
        await query.edit_message_text(t(lang, "choose_lang"), reply_markup=lang_kb())
        return

    if data == "set:family":
        context.user_data["awaiting"] = "set_family"
        await query.edit_message_text(t(lang, "ask_family_size"), reply_markup=back_kb(lang))
        return

    if data == "set:allergies":
        context.user_data["awaiting"] = "set_allergies"
        await query.edit_message_text(t(lang, "ask_allergies"), reply_markup=back_kb(lang))
        return

    if data == "set:dislikes":
        context.user_data["awaiting"] = "set_dislikes"
        await query.edit_message_text(t(lang, "ask_dislikes"), reply_markup=back_kb(lang))
        return


# ---------------------------------------------------------------------------
# Экраны с данными (любимые блюда / список покупок / настройки)
# ---------------------------------------------------------------------------

async def show_favorites(query, lang, user_id, edit=False):
    favs = storage.list_favorites(user_id)
    if favs:
        body = "\n".join(t(lang, "favorites_list_item", member=f["member"], dish=f["dish"]) for f in favs)
    else:
        body = t(lang, "favorites_empty")
    text = f"{t(lang, 'favorites_title')}\n\n{body}"

    rows = [[InlineKeyboardButton(t(lang, "btn_add_favorite"), callback_data="fav:add")]]
    for f in favs:
        rows.append([InlineKeyboardButton(
            f"🗑 {f['member']}: {f['dish']}", callback_data=f"fav:remove:{f['id']}"
        )])
    rows.append([InlineKeyboardButton(t(lang, "back_to_menu"), callback_data="menu:main")])
    kb = InlineKeyboardMarkup(rows)

    if edit:
        await query.edit_message_text(text, reply_markup=kb)
    else:
        await query.message.reply_text(text, reply_markup=kb)


async def show_shoplist(query, lang, user_id, edit=False):
    items = storage.get_shopping_list(user_id)
    if items:
        body = "\n".join(f"• {i['item']}" for i in items)
    else:
        body = t(lang, "shoplist_empty")
    text = f"{t(lang, 'shoplist_title')}\n\n{body}"

    rows = [
        [InlineKeyboardButton(t(lang, "btn_add_shoplist"), callback_data="shop:add")],
        [InlineKeyboardButton(t(lang, "btn_clear_shoplist"), callback_data="shop:clear")],
        [InlineKeyboardButton(t(lang, "back_to_menu"), callback_data="menu:main")],
    ]
    kb = InlineKeyboardMarkup(rows)

    if edit:
        await query.edit_message_text(text, reply_markup=kb)
    else:
        await query.message.reply_text(text, reply_markup=kb)


async def show_settings(query, lang, user_id, edit=False):
    user = storage.get_user(user_id)
    text = f"{t(lang, 'settings_title')}\n\n" + t(
        lang, "settings_summary",
        lang="Русский" if lang == "ru" else "O'zbekcha",
        family_size=user["family_size"],
        allergies=user["allergies"] or t(lang, "none"),
        dislikes=user["dislikes"] or t(lang, "none"),
    )
    rows = [
        [InlineKeyboardButton(t(lang, "btn_change_lang"), callback_data="set:lang")],
        [InlineKeyboardButton(t(lang, "btn_set_family_size"), callback_data="set:family")],
        [InlineKeyboardButton(t(lang, "btn_set_allergies"), callback_data="set:allergies")],
        [InlineKeyboardButton(t(lang, "btn_set_dislikes"), callback_data="set:dislikes")],
        [InlineKeyboardButton(t(lang, "back_to_menu"), callback_data="menu:main")],
    ]
    kb = InlineKeyboardMarkup(rows)
    if edit:
        await query.edit_message_text(text, reply_markup=kb)
    else:
        await query.message.reply_text(text, reply_markup=kb)


# ---------------------------------------------------------------------------
# Обработка текстовых сообщений (ответы на "ask_*")
# ---------------------------------------------------------------------------

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not storage.has_user(user_id):
        await update.message.reply_text(t("ru", "choose_lang"), reply_markup=lang_kb())
        return

    lang = get_lang(user_id)
    awaiting = context.user_data.get("awaiting")
    text_in = update.message.text.strip()

    if awaiting == "ingredients":
        context.user_data["awaiting"] = None
        prompt = f"Вот что есть дома: {text_in}. Что можно из этого приготовить?"
        await generate_and_send(update.message, context, lang, user_id, prompt)
        return

    if awaiting == "product_other":
        context.user_data["awaiting"] = None
        prompt = f"Предложи рецепты, где основной продукт — {text_in}."
        await generate_and_send(update.message, context, lang, user_id, prompt)
        return

    if awaiting == "missing_have":
        context.user_data["awaiting"] = None
        prompt = f"Дома есть: {text_in}."
        await process_missing_ingredients(update.message, context, lang, user_id, prompt)
        return

    if awaiting == "people_other":
        context.user_data["awaiting"] = "people_dish"
        context.user_data["people_n"] = text_in
        await update.message.reply_text(t(lang, "ask_people_dish", n=text_in), reply_markup=back_kb(lang))
        return

    if awaiting == "people_dish":
        context.user_data["awaiting"] = None
        n = context.user_data.get("people_n", "?")
        prompt = f"Нужно приготовить на {n} человек. Вот что есть/что хочется: {text_in}. Дай рецепт с пересчитанными пропорциями на {n} порций."
        await generate_and_send(update.message, context, lang, user_id, prompt)
        return

    if awaiting == "budget_other":
        context.user_data["awaiting"] = None
        prompt = f"Бюджет на сегодняшний ужин — примерно {text_in} сум. Предложи блюда, в которые можно уложиться на ташкентском базаре."
        await generate_and_send(update.message, context, lang, user_id, prompt)
        return

    if awaiting == "fav_add":
        context.user_data["awaiting"] = None
        sep = None
        for candidate in ["—", "-", ":"]:
            if candidate in text_in:
                sep = candidate
                break
        if not sep:
            await update.message.reply_text(t(lang, "favorite_bad_format"), reply_markup=back_kb(lang))
            return
        member, dish = text_in.split(sep, 1)
        storage.add_favorite(user_id, member.strip(), dish.strip())
        await update.message.reply_text(t(lang, "favorite_added"))
        await show_favorites(update.message, lang, user_id, edit=False)
        return

    if awaiting == "shop_add":
        context.user_data["awaiting"] = None
        items = [x.strip() for x in text_in.split(",") if x.strip()]
        storage.add_shopping_items(user_id, items)
        await update.message.reply_text(t(lang, "added_to_shoplist"))
        await show_shoplist(update.message, lang, user_id, edit=False)
        return

    if awaiting == "set_family":
        context.user_data["awaiting"] = None
        try:
            size = int(text_in)
            storage.set_family_size(user_id, size)
            await update.message.reply_text(t(lang, "settings_saved"))
        except ValueError:
            await update.message.reply_text(t(lang, "not_understood"))
        await show_settings(update.message, lang, user_id, edit=False)
        return

    if awaiting == "set_allergies":
        context.user_data["awaiting"] = None
        value = "" if text_in.lower() in ("нет", "yo'q", "yoq", "-") else text_in
        storage.set_allergies(user_id, value)
        await update.message.reply_text(t(lang, "settings_saved"))
        await show_settings(update.message, lang, user_id, edit=False)
        return

    if awaiting == "set_dislikes":
        context.user_data["awaiting"] = None
        value = "" if text_in.lower() in ("нет", "yo'q", "yoq", "-") else text_in
        storage.set_dislikes(user_id, value)
        await update.message.reply_text(t(lang, "settings_saved"))
        await show_settings(update.message, lang, user_id, edit=False)
        return

    # если ничего не ждём — считаем, что это список продуктов "что есть дома"
    prompt = f"Вот что есть дома: {text_in}. Что можно из этого приготовить?"
    await generate_and_send(update.message, context, lang, user_id, prompt)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not storage.has_user(user_id):
        await update.message.reply_text(t("ru", "choose_lang"), reply_markup=lang_kb())
        return

    lang = get_lang(user_id)
    awaiting = context.user_data.get("awaiting")
    image_bytes = await download_photo_bytes(update)
    caption = (update.message.caption or "").strip()

    if awaiting == "missing_have":
        context.user_data["awaiting"] = None
        prompt = "На фото — продукты, которые есть дома." + (f" Дополнение от пользователя: {caption}." if caption else "")
        await process_missing_ingredients(update.message, context, lang, user_id, prompt, image_bytes=image_bytes)
        return

    # по умолчанию (в т.ч. после кнопки "Что есть дома") — фото трактуем как список продуктов
    context.user_data["awaiting"] = None
    prompt = "На фото — продукты для готовки. Определи, что на нём есть, и предложи, что из этого приготовить."
    if caption:
        prompt += f" Дополнение от пользователя: {caption}."
    await generate_and_send(update.message, context, lang, user_id, prompt, image_bytes=image_bytes)


async def handle_add_missing_to_shoplist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    lang = get_lang(user_id)
    items = context.user_data.get("pending_missing_items", [])
    if items:
        storage.add_shopping_items(user_id, items)
    context.user_data["pending_missing_items"] = []
    await query.edit_message_text(t(lang, "added_to_shoplist"), reply_markup=back_kb(lang))


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    storage.init_db()
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_add_missing_to_shoplist, pattern=r"^shop:addmissing$"))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Бот запущен")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
