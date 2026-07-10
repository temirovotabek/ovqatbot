# -*- coding: utf-8 -*-
"""
Бесплатный поиск фото блюда по названию через Wikimedia Commons.
Не требует API-ключа. Лучшее старание: если фото не нашлось — просто
возвращаем None, и бот отправляет только текст рецепта.
"""
import requests

COMMONS_API = "https://commons.wikimedia.org/w/api.php"


def find_dish_image_url(query: str):
    try:
        resp = requests.get(
            COMMONS_API,
            params={
                "action": "query",
                "generator": "search",
                "gsrnamespace": 6,  # namespace файлов
                "gsrsearch": f"{query} food dish",
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
