# -*- coding: utf-8 -*-
"""
Бесплатный поиск фото блюда по названию через Wikimedia Commons.
Не требует API-ключа. Лучшее старание: если фото не нашлось — просто
возвращаем None, и бот отправляет только текст рецепта.

Название блюда сначала переводится на английский через Groq (тот же
ключ, что и для рецептов) — Wikimedia Commons плохо ищет по русским/
узбекским запросам, а по английским находит заметно чаще.
"""
import os

import requests
from groq import Groq

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
TRANSLATE_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _client


def _translate_to_english(dish_name: str) -> str:
    """Лучшее старание: если перевод не удался — используем исходное название."""
    try:
        client = _get_client()
        resp = client.chat.completions.create(
            model=TRANSLATE_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Переведи название блюда на английский язык. Ответь ТОЛЬКО переводом, без кавычек и пояснений.",
                },
                {"role": "user", "content": dish_name},
            ],
            max_tokens=20,
            temperature=0,
        )
        translated = (resp.choices[0].message.content or "").strip()
        return translated or dish_name
    except Exception:
        return dish_name


def find_dish_image_url(query: str):
    search_query = _translate_to_english(query)
    try:
        resp = requests.get(
            COMMONS_API,
            params={
                "action": "query",
                "generator": "search",
                "gsrnamespace": 6,  # namespace файлов
                "gsrsearch": f"{search_query} food dish",
                "gsrlimit": 1,
                "prop": "imageinfo",
                "iiprop": "url",
                "iiurlwidth": 800,
                "format": "json",
            },
            timeout=8,
        )
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            imageinfo = page.get("imageinfo")
            if imageinfo:
                return imageinfo[0].get("thumburl") or imageinfo[0].get("url")
    except Exception:
        pass
    return None
