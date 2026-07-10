# -*- coding: utf-8 -*-
"""
Все тексты интерфейса бота на двух языках: ru и uz (узбекская латиница).
Если нужна кириллица — просто поменяй значения в словаре T["uz"].
"""

T = {
    "ru": {
        "choose_lang": "Привет! На каком языке тебе удобнее? / Qaysi tilda qulay?",
        "lang_set": "Готово! Буду общаться на русском 🇷🇺",
        "ask_name": "Как тебя зовут?",
        "name_saved": "Приятно познакомиться, {name}! 😊",
        "hello_name": "Привет, {name}!",
        "ai_error": "Сервис сейчас перегружен, попробуй ещё раз через минуту 🙏",
        "main_menu_title": "🍳 Что приготовить?\n\nВыбери, с чем помочь:",
        "back_to_menu": "🔙 Главное меню",

        "btn_ingredients": "🔍 Что есть дома",
        "btn_quick": "⏱ Быстрые рецепты",
        "btn_byproduct": "🍗 По продукту",
        "btn_surprise": "🎲 Удиви меня",
        "btn_missing": "🛒 Не хватает ингредиентов",
        "btn_people": "👨‍👩‍👧 На сколько человек",
        "btn_mood": "😋 По настроению",
        "btn_budget": "💰 По бюджету",
        "btn_weekmenu": "📅 Меню на неделю",
        "btn_favorites": "❤️ Любимые блюда",
        "btn_shoplist": "🛍 Список покупок",
        "btn_settings": "⚙️ Настройки",

        "ask_ingredients": "Напиши, что есть дома (через запятую), или пришли фото продуктов 📷\nНапример: курица, картошка, лук, помидоры",
        "generating": "Готовлю варианты… 🍲",

        "ask_time": "Сколько времени есть на готовку?",
        "time_15": "15 минут",
        "time_30": "30 минут",
        "time_60": "1 час",
        "time_any": "Неважно",

        "ask_product": "Что хочешь использовать как основу?",
        "product_chicken": "🍗 Курица",
        "product_beef": "🥩 Говядина",
        "product_fish": "🐟 Рыба",
        "product_potato": "🥔 Картофель",
        "product_veg": "🥦 Овощи",
        "product_pasta": "🍝 Макароны",
        "product_other": "✍️ Другое",
        "ask_product_other": "Напиши, какой продукт хочешь использовать:",

        "ask_missing_have": "Напиши, что уже есть дома, или пришли фото продуктов 📷",
        "missing_result_prefix": "Вот что можно приготовить, а вот чего не хватает:",
        "btn_add_to_shoplist": "➕ Добавить недостающее в список покупок",
        "added_to_shoplist": "Добавлено в список покупок ✅",

        "ask_people": "На сколько человек готовим сегодня?",
        "people_2": "2", "people_3": "3", "people_4": "4", "people_6": "6", "people_other": "Другое",
        "ask_people_other": "Напиши число человек:",
        "ask_people_dish": "На {n} человек. А теперь напиши, из чего готовим (или просто пришли название блюда):",

        "ask_mood": "Чего хочется?",
        "mood_light": "🥗 Легкое",
        "mood_hearty": "🍖 Сытное",
        "mood_healthy": "🥦 Полезное",
        "mood_spicy": "🌶 Острое",
        "mood_sweet": "🍰 Сладкое",

        "ask_budget": "Какой бюджет на сегодня (в сумах)?",
        "budget_50k": "50 000",
        "budget_100k": "100 000",
        "budget_200k": "200 000",
        "budget_other": "Своя сумма",
        "ask_budget_other": "Напиши сумму в сумах:",

        "weekmenu_generating": "Составляю меню на неделю с учётом ваших предпочтений… 📅",

        "favorites_title": "❤️ Любимые блюда семьи",
        "favorites_empty": "Пока пусто. Добавь, кто что любит — бот будет учитывать это в рецептах.",
        "favorites_list_item": "• {member}: {dish}",
        "btn_add_favorite": "➕ Добавить",
        "btn_remove_favorite": "🗑 Удалить",
        "ask_add_favorite": "Напиши в формате:\nкто — блюдо\n\nНапример: муж — донер",
        "favorite_added": "Добавлено ✅",
        "ask_remove_favorite": "Выбери, что удалить:",
        "favorite_removed": "Удалено ✅",
        "favorite_bad_format": "Не понял формат. Напиши так: муж — донер",

        "shoplist_title": "🛍 Список покупок",
        "shoplist_empty": "Список покупок пуст.",
        "btn_clear_shoplist": "🗑 Очистить список",
        "shoplist_cleared": "Список очищен ✅",
        "ask_add_shoplist": "Напиши, что добавить в список (через запятую):",
        "btn_add_shoplist": "➕ Добавить вручную",

        "settings_title": "⚙️ Настройки",
        "settings_summary": (
            "Язык: {lang}\n"
            "Размер семьи по умолчанию: {family_size}\n"
            "Аллергии: {allergies}\n"
            "Не любим: {dislikes}"
        ),
        "btn_change_lang": "🌐 Язык",
        "btn_set_family_size": "👨‍👩‍👧 Размер семьи",
        "btn_set_allergies": "⚠️ Аллергии",
        "btn_set_dislikes": "🚫 Не любим",
        "ask_family_size": "Сколько человек в семье обычно?",
        "ask_allergies": "Напиши через запятую, на что аллергия (или «нет»):",
        "ask_dislikes": "Напиши через запятую, что не любите (или «нет»):",
        "settings_saved": "Сохранено ✅",

        "not_understood": "Не поняла 🙈 Выбери пункт меню кнопкой ниже.",
        "none": "нет",
    },

    "uz": {
        "choose_lang": "Salom! Qaysi tilda qulay? / На каком языке тебе удобнее?",
        "lang_set": "Ajoyib! Endi o'zbek tilida gaplashamiz 🇺🇿",
        "ask_name": "Ismingiz nima?",
        "name_saved": "Tanishganimdan xursandman, {name}! 😊",
        "hello_name": "Salom, {name}!",
        "ai_error": "Xizmat hozir band, bir daqiqadan keyin qayta urinib ko'ring 🙏",
        "main_menu_title": "🍳 Nima pishiray?\n\nNimada yordam beray:",
        "back_to_menu": "🔙 Bosh menyu",

        "btn_ingredients": "🔍 Uyda nima bor",
        "btn_quick": "⏱ Tez retseptlar",
        "btn_byproduct": "🍗 Mahsulot bo'yicha",
        "btn_surprise": "🎲 Meni hayron qoldir",
        "btn_missing": "🛒 Yetishmayotgan mahsulotlar",
        "btn_people": "👨‍👩‍👧 Necha kishiga",
        "btn_mood": "😋 Kayfiyat bo'yicha",
        "btn_budget": "💰 Byudjet bo'yicha",
        "btn_weekmenu": "📅 Haftalik menyu",
        "btn_favorites": "❤️ Sevimli taomlar",
        "btn_shoplist": "🛍 Xarid ro'yxati",
        "btn_settings": "⚙️ Sozlamalar",

        "ask_ingredients": "Uyda nima borligini yoz (vergul bilan) yoki mahsulotlar fotosini yubor 📷\nMasalan: tovuq, kartoshka, piyoz, pomidor",
        "generating": "Variantlarni tayyorlayapman… 🍲",

        "ask_time": "Ovqat pishirishga qancha vaqting bor?",
        "time_15": "15 daqiqa",
        "time_30": "30 daqiqa",
        "time_60": "1 soat",
        "time_any": "Farqi yo'q",

        "ask_product": "Asosiy mahsulot sifatida nimani ishlatmoqchisan?",
        "product_chicken": "🍗 Tovuq",
        "product_beef": "🥩 Mol go'shti",
        "product_fish": "🐟 Baliq",
        "product_potato": "🥔 Kartoshka",
        "product_veg": "🥦 Sabzavotlar",
        "product_pasta": "🍝 Makaron",
        "product_other": "✍️ Boshqa",
        "ask_product_other": "Qaysi mahsulotni ishlatmoqchi ekaningni yoz:",

        "ask_missing_have": "Uyda nima borligini yoz yoki mahsulotlar fotosini yubor 📷",
        "missing_result_prefix": "Mana nima pishirish mumkin va nimalar yetishmayapti:",
        "btn_add_to_shoplist": "➕ Yetishmaganini xarid ro'yxatiga qo'shish",
        "added_to_shoplist": "Xarid ro'yxatiga qo'shildi ✅",

        "ask_people": "Bugun necha kishiga pishiramiz?",
        "people_2": "2", "people_3": "3", "people_4": "4", "people_6": "6", "people_other": "Boshqa",
        "ask_people_other": "Kishilar sonini yoz:",
        "ask_people_dish": "{n} kishiga. Endi nimadan pishirishni yoz (yoki taom nomini yubor):",

        "ask_mood": "Nima yeging keldi?",
        "mood_light": "🥗 Yengil",
        "mood_hearty": "🍖 To'yimli",
        "mood_healthy": "🥦 Foydali",
        "mood_spicy": "🌶 Achchiq",
        "mood_sweet": "🍰 Shirin",

        "ask_budget": "Bugungi byudjet qancha (so'mda)?",
        "budget_50k": "50 000",
        "budget_100k": "100 000",
        "budget_200k": "200 000",
        "budget_other": "Boshqa summa",
        "ask_budget_other": "Summani so'mda yoz:",

        "weekmenu_generating": "Oilangiz didini hisobga olib haftalik menyu tuzyapman… 📅",

        "favorites_title": "❤️ Oilaning sevimli taomlari",
        "favorites_empty": "Hozircha bo'sh. Kim nimani yaxshi ko'rishini qo'sh — bot buni retseptlarda hisobga oladi.",
        "favorites_list_item": "• {member}: {dish}",
        "btn_add_favorite": "➕ Qo'shish",
        "btn_remove_favorite": "🗑 O'chirish",
        "ask_add_favorite": "Shu formatda yoz:\nkim — taom\n\nMasalan: er — doner",
        "favorite_added": "Qo'shildi ✅",
        "ask_remove_favorite": "Nimani o'chirishni tanla:",
        "favorite_removed": "O'chirildi ✅",
        "favorite_bad_format": "Formatni tushunmadim. Shunday yoz: er — doner",

        "shoplist_title": "🛍 Xarid ro'yxati",
        "shoplist_empty": "Xarid ro'yxati bo'sh.",
        "btn_clear_shoplist": "🗑 Ro'yxatni tozalash",
        "shoplist_cleared": "Ro'yxat tozalandi ✅",
        "ask_add_shoplist": "Ro'yxatga nima qo'shishni yoz (vergul bilan):",
        "btn_add_shoplist": "➕ Qo'lda qo'shish",

        "settings_title": "⚙️ Sozlamalar",
        "settings_summary": (
            "Til: {lang}\n"
            "Oila hajmi (standart): {family_size}\n"
            "Allergiya: {allergies}\n"
            "Yoqtirmaymiz: {dislikes}"
        ),
        "btn_change_lang": "🌐 Til",
        "btn_set_family_size": "👨‍👩‍👧 Oila hajmi",
        "btn_set_allergies": "⚠️ Allergiya",
        "btn_set_dislikes": "🚫 Yoqtirmaymiz",
        "ask_family_size": "Oilada odatda necha kishi bo'ladi?",
        "ask_allergies": "Vergul bilan nimaga allergiya borligini yoz (yoki «yo'q»):",
        "ask_dislikes": "Vergul bilan nimani yoqtirmasligingizni yoz (yoki «yo'q»):",
        "settings_saved": "Saqlandi ✅",

        "not_understood": "Tushunmadim 🙈 Quyidagi menyudan tanla.",
        "none": "yo'q",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    lang = lang if lang in T else "ru"
    text = T[lang].get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text
