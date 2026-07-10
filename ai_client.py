# -*- coding: utf-8 -*-
"""
Обращение к Google Gemini API за рецептами — текст и/или фото продуктов.

Почему Gemini, а не Claude: у Google есть по-настоящему бесплатный тариф
(Google AI Studio), который включает и работу с изображениями. У Claude API
бесплатного тарифа нет — там платят за каждый запрос.

Бесплатный тариф Gemini (модель gemini-2.5-flash, на июль 2026):
  ~10 запросов в минуту, 1500 запросов в сутки — для одной семьи это
  огромный запас, кончиться не должно.

⚠️ Важный нюанс бесплатного тарифа: Google может использовать присланные
   фото и тексты для улучшения своих моделей (в отличие от платного
   тарифа). Если это критично — можно включить биллинг в Google Cloud
   (тогда действуют более приватные условия), но тогда тариф перестанет
   быть бесплатным. Для семейного бота с фото содержимого холодильника
   это обычно не проблема, но лучше знать заранее.
"""
import os
import re
import time

from google import genai
from google.genai import types

MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")

_client = None


def get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


LANG_NAME = {
    "ru": "русском",
    "uz": "узбекском (латиница)",
}


def build_system_prompt(lang: str, user_ctx: dict) -> str:
    allergies = user_ctx.get("allergies") or ""
    dislikes = user_ctx.get("dislikes") or ""
    favorites = user_ctx.get("favorites") or []
    recent = user_ctx.get("recent_history") or []
    name = user_ctx.get("name") or ""

    favorites_txt = "; ".join(f"{f['member']} любит {f['dish']}" for f in favorites) or "нет данных"
    recent_txt = ", ".join(recent) or "нет"
    name_txt = f"Пользователя зовут {name}, можешь иногда обращаться по имени." if name else ""

    lang_name = LANG_NAME.get(lang, "русском")

    return f"""Ты — кулинарный помощник семьи, живущей в Ташкенте, Узбекистан.
Отвечай ТОЛЬКО на {lang_name} языке, независимо от языка запроса.
{name_txt}

Правила:
- Продукты покупаются на местном узбекском базаре и в обычных магазинах Ташкента — не предлагай
  экзотику, которую трудно найти в Узбекистане, но НЕ ограничивайся только узбекской кухней.
  Свободно предлагай блюда из разных кухонь мира — итальянской, азиатской, кавказской, турецкой,
  европейской и т.д. — если ингредиенты это позволяют. Узбекские блюда (плов, лагман, манты, шурпа,
  самса, чучвара, норин) предлагай наравне с остальными, а не как единственный вариант.
- Старайся разнообразить предложения: если из одних и тех же продуктов можно сделать и узбекское,
  и не-узбекское блюдо — предложи и то, и другое среди вариантов.
- Если на входе есть фото — сначала кратко перечисли, что ты на нём распознал (список продуктов),
  а затем уже переходи к рецептам. Если что-то на фото распознать не удалось — так и скажи, не выдумывай.
- Формат ответа — удобный для Telegram: используй *жирный* для названий блюд, эмодзи для ориентира,
  указывай примерное время готовки и количество порций.
- Будь краток и практичен: 2-4 варианта блюд, без длинных вступлений.
- В конце каждого блюда коротко перечисли шаги (не более 5-6 пунктов).
- Аллергии семьи (обязательно исключи эти продукты): {allergies or 'нет'}.
- Не любят (по возможности избегай): {dislikes or 'нет'}.
- Любимые блюда членов семьи (учитывай, можно предлагать похожее, но не приедающееся): {favorites_txt}.
- Недавно уже предлагались блюда, старайся НЕ повторять их: {recent_txt}.
"""


def _extract_dish_titles(text: str):
    """Достаёт названия блюд из ответа (то, что в *жирном*), чтобы запомнить в историю."""
    titles = re.findall(r"\*([^*\n]{3,60})\*", text)
    return titles[:6]


def ask(lang: str, user_ctx: dict, user_prompt: str, image_bytes: bytes = None):
    """Отправляет запрос в Gemini (текст и, опционально, фото), возвращает (текст, названия_блюд).

    На бесплатном тарифе модель иногда отвечает 503 (сервер перегружен) — это
    временная проблема на стороне Google. Делаем до 3 попыток с паузой.
    """
    client = get_client()
    system = build_system_prompt(lang, user_ctx)

    parts = []
    if image_bytes:
        parts.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))
    parts.append(types.Part.from_text(text=user_prompt))

    last_error = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=parts,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    max_output_tokens=1500,
                ),
            )
            text = response.text or ""
            titles = _extract_dish_titles(text)
            return text, titles
        except Exception as e:
            last_error = e
            if attempt < 2:
                time.sleep(4)
                continue
    raise last_error
