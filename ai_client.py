# -*- coding: utf-8 -*-
import os
import re
from groq import Groq

MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
_client = None

def get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _client

LANG_NAME = {"ru": "русском", "uz": "узбекском (латиница)"}

def build_system_prompt(lang, user_ctx):
    allergies = user_ctx.get("allergies") or ""
    dislikes = user_ctx.get("dislikes") or ""
    favorites = user_ctx.get("favorites") or []
    recent = user_ctx.get("recent_history") or []
    name = user_ctx.get("name") or ""
    family_size = user_ctx.get("family_size") or 4
    fav_txt = "; ".join(f"{f['member']} любит {f['dish']}" for f in favorites) or "не указаны"
    recent_txt = ", ".join(recent) or "нет"
    name_line = f"Пользователя зовут {name} — иногда обращайся по имени, но не в каждом сообщении." if name else ""
    lang_name = LANG_NAME.get(lang, "русском")
    return f"""Ты — кулинарный помощник семьи из Ташкента (Узбекистан).
Отвечай ТОЛЬКО на {lang_name} языке.
{name_line}

СТИЛЬ: пиши живо и по-человечески — как умный друг, который хорошо готовит.
Можно немного пошутить или добавить тёплый комментарий, но главное — практичность.
Не пиши как робот.

КУХНЯ: предлагай блюда из РАЗНЫХ кухонь — узбекскую (плов, лагман, манты, шурпа, самса),
итальянскую (паста, ризотто), азиатскую (вок, жареный рис), кавказскую, турецкую, европейскую.
Продукты должны быть доступны на ташкентском базаре.

ФОРМАТ для Telegram:
- Названия блюд выдели *жирным*
- Укажи время и порции (семья {family_size} чел.)
- 2-4 варианта, шаги кратко (до 5-6 пунктов)
- Без длинных вступлений

ОГРАНИЧЕНИЯ:
- Аллергии: {allergies or 'нет'}
- Не любят: {dislikes or 'нет'}
- Любимые блюда: {fav_txt}
- Недавно предлагалось (не повторяй): {recent_txt}
"""

def _extract_dish_titles(text):
    return re.findall(r"\*([^*\n]{3,60})\*", text)[:6]

def ask(lang, user_ctx, user_prompt, image_bytes=None):
    client = get_client()
    system = build_system_prompt(lang, user_ctx)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1200,
        temperature=0.8,
    )
    text = response.choices[0].message.content or ""
    return text, _extract_dish_titles(text)
