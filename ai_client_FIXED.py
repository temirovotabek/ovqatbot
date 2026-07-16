# -*- coding: utf-8 -*-
"""
Генерация рецептов через Groq API (бесплатно, без ограничений по IP/новым ключам).

Модель: llama-3.3-70b-versatile — та же, что в боте "Что приготовить?" для жены.
Ключ: бесплатно на https://console.groq.com → API Keys (вход через Google-аккаунт).
Лимит бесплатного тарифа: ~14400 запросов в сутки — с головой хватит.

ФИКС 2026-07-16 (Sherlock): узбекский ответ модели иногда мешал кириллицу
и латиницу в одном слове ('нIMA', 'чIQamiz') — инструкция 'узбекском
(латиница)' слишком слабая, Groq/llama-3.3-70b периодически съезжает в
кириллицу (её больше в обучающих данных для узбекского). Вместо того чтобы
полагаться на модель, после получения ответа для lang=='uz' текст
принудительно прогоняется через детерминированную транслитерацию
кириллица -> латиница (_transliterate_uz). Результат гарантированно
латиница независимо от того, каким скриптом реально ответила модель.
Не идеально по регистру в редких случаях (если модель сама смешала
регистр внутри слова) — но проблема смешения СКРИПТОВ решена полностью.
"""
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


LANG_NAME = {
    "ru": "русском",
    "uz": "узбекском языке, ТОЛЬКО латинским алфавитом (o'zbek lotin alifbosi), "
    "например: 'Salom, bugun osh tayyorlaymiz'. Ни одной кириллической буквы быть не должно",
}

# Детерминированная транслитерация узбекская кириллица -> латиница.
# Ключи — строчные кириллические буквы; латинские символы в мапу не входят
# и проходят через _transliterate_uz без изменений, поэтому функцию можно
# безопасно применять к тексту, где модель и так частично написала латиницей.
_UZ_CYR_TO_LAT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "j", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "x", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sh",
    "ъ": "'", "ы": "i", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    # узбекские спецбуквы
    "ў": "o'", "қ": "q", "ғ": "g'", "ҳ": "h",
}


def _transliterate_uz(text: str) -> str:
    result = []
    for ch in text:
        lower = ch.lower()
        repl = _UZ_CYR_TO_LAT.get(lower)
        if repl is None:
            result.append(ch)
            continue
        if ch.isupper() and repl:
            repl = repl[0].upper() + repl[1:]
        result.append(repl)
    return "".join(result)


def build_system_prompt(lang: str, user_ctx: dict) -> str:
    allergies = user_ctx.get("allergies") or ""
    dislikes   = user_ctx.get("dislikes") or ""
    favorites  = user_ctx.get("favorites") or []
    recent     = user_ctx.get("recent_history") or []
    name       = user_ctx.get("name") or ""
    family_size = user_ctx.get("family_size") or 4

    fav_txt    = "; ".join(f"{f['member']} любит {f['dish']}" for f in favorites) or "не указаны"
    recent_txt = ", ".join(recent) or "нет"
    name_line  = f"Пользователя зовут {name} — иногда обращайся по имени, но не в каждом сообщении." if name else ""

    lang_name = LANG_NAME.get(lang, "русском")

    return f"""Ты — кулинарный помощник семьи из Ташкента (Узбекистан).
Отвечай ТОЛЬКО на {lang_name} языке.
{name_line}

СТИЛЬ: пиши живо и по-человечески — как умный друг, который хорошо готовит.
Можно немного пошутить или добавить тёплый комментарий, но главное — практичность.
Не пиши как робот, не используй казённые фразы типа «Конечно, вот рецепт:».

КУХНЯ: предлагай блюда из РАЗНЫХ кухонь мира — узбекскую (плов, лагман, манты, шурпа,
самса, норин, чучвара), итальянскую (паста, ризотто), азиатскую (жареный рис, вок),
кавказскую, турецкую, европейскую и т.д. Узбекские блюда — не единственный вариант.
Продукты должны быть доступны на ташкентском базаре и в обычных магазинах.

ФОРМАТ (важно для Telegram):
- Названия блюд выдели *жирным*
- Укажи время приготовления и на сколько порций (семья {family_size} чел.)
- 1-2 варианта блюд (лучше меньше, но подробно, чем много и поверхностно)
- Шаги — пошагово и по делу, не бойся расписать важные детали (температура, время, на что обратить внимание)
- Без длинных вступлений — сразу к делу

ОГРАНИЧЕНИЯ:
- Аллергии (исключи): {allergies or 'нет'}
- Не любят: {dislikes or 'нет'}
- Любимые блюда семьи (учитывай): {fav_txt}
- Недавно предлагалось (не повторяй): {recent_txt}
"""


def _extract_dish_titles(text: str):
    titles = re.findall(r"\*([^*\n]{3,60})\*", text)
    return titles[:6]


def ask(lang: str, user_ctx: dict, user_prompt: str, image_bytes: bytes = None):
    """
    Запрос к Groq. image_bytes игнорируется (Groq пока не поддерживает vision
    на бесплатном тарифе) — оставлен для совместимости с сигнатурой функции.
    """
    client = get_client()
    system = build_system_prompt(lang, user_ctx)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user_prompt},
        ],
        max_tokens=1600,
        temperature=0.8,
    )

    text = response.choices[0].message.content or ""
    if lang == "uz":
        text = _transliterate_uz(text)
    titles = _extract_dish_titles(text)
    return text, titles
