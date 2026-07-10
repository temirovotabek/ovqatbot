# -*- coding: utf-8 -*-
"""
Хранение данных бота в SQLite.

ВАЖНО про Railway: файловая система контейнера сбрасывается при каждом
редеплое, если не подключён постоянный Volume. Чтобы данные (язык, любимые
блюда, список покупок) не терялись — подключи Railway Volume и укажи путь
к нему в переменной окружения DB_PATH (например /data/bot.db).
"""
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta

DB_PATH = os.environ.get("DB_PATH", "bot.db")

DEFAULT_FAMILY_SIZE = 4


def init_db():
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'ru',
                family_size INTEGER DEFAULT 4,
                allergies TEXT DEFAULT '',
                dislikes TEXT DEFAULT '',
                name TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                member TEXT,
                dish TEXT
            );

            CREATE TABLE IF NOT EXISTS shopping_list (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item TEXT
            );

            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                dish_title TEXT,
                created_at TEXT
            );
            """
        )
        # Миграция: если база создана раньше (без колонки name), добавляем её
        try:
            conn.execute("ALTER TABLE users ADD COLUMN name TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass  # колонка уже существует


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ---------- users ----------

def get_user(user_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO users (user_id, family_size) VALUES (?, ?)",
                (user_id, DEFAULT_FAMILY_SIZE),
            )
            row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        return dict(row)


def has_user(user_id: int) -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,)).fetchone()
        return row is not None


def set_language(user_id: int, lang: str):
    get_user(user_id)
    with get_conn() as conn:
        conn.execute("UPDATE users SET language=? WHERE user_id=?", (lang, user_id))


def set_name(user_id: int, name: str):
    get_user(user_id)
    with get_conn() as conn:
        conn.execute("UPDATE users SET name=? WHERE user_id=?", (name, user_id))


def set_family_size(user_id: int, size: int):
    get_user(user_id)
    with get_conn() as conn:
        conn.execute("UPDATE users SET family_size=? WHERE user_id=?", (size, user_id))


def set_allergies(user_id: int, text: str):
    get_user(user_id)
    with get_conn() as conn:
        conn.execute("UPDATE users SET allergies=? WHERE user_id=?", (text, user_id))


def set_dislikes(user_id: int, text: str):
    get_user(user_id)
    with get_conn() as conn:
        conn.execute("UPDATE users SET dislikes=? WHERE user_id=?", (text, user_id))


# ---------- favorites ----------

def add_favorite(user_id: int, member: str, dish: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO favorites (user_id, member, dish) VALUES (?, ?, ?)",
            (user_id, member.strip(), dish.strip()),
        )


def list_favorites(user_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM favorites WHERE user_id=? ORDER BY id", (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def remove_favorite(favorite_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM favorites WHERE id=?", (favorite_id,))


# ---------- shopping list ----------

def add_shopping_items(user_id: int, items):
    with get_conn() as conn:
        for item in items:
            item = item.strip()
            if item:
                conn.execute(
                    "INSERT INTO shopping_list (user_id, item) VALUES (?, ?)",
                    (user_id, item),
                )


def get_shopping_list(user_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM shopping_list WHERE user_id=? ORDER BY id", (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def clear_shopping_list(user_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM shopping_list WHERE user_id=?", (user_id,))


# ---------- history (чтобы не повторять одни и те же блюда) ----------

def add_history(user_id: int, dish_titles):
    with get_conn() as conn:
        now = datetime.utcnow().isoformat()
        for title in dish_titles:
            title = title.strip()
            if title:
                conn.execute(
                    "INSERT INTO history (user_id, dish_title, created_at) VALUES (?, ?, ?)",
                    (user_id, title, now),
                )
        # чистим старую историю (старше 30 дней), чтобы таблица не росла бесконечно
        cutoff = (datetime.utcnow() - timedelta(days=30)).isoformat()
        conn.execute("DELETE FROM history WHERE user_id=? AND created_at<?", (user_id, cutoff))


def recent_history(user_id: int, limit: int = 15):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT dish_title FROM history WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [r["dish_title"] for r in rows]
