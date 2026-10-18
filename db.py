import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = "freelance.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                task_type TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        conn.commit()

def add_task(platform: str, task_type: str, description: str, amount: float, status: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO tasks (platform, task_type, description, amount, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (platform, task_type, description, amount, status, now))
        conn.commit()
        return cursor.lastrowid

def get_last_tasks(limit=10):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tasks ORDER BY id DESC LIMIT ?', (limit,))
        return cursor.fetchall()

def update_task_status(task_id: int, status: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE tasks SET status = ? WHERE id = ?', (status, task_id))
        conn.commit()

def delete_task(task_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()

def get_stats():
    now = datetime.now()
    today_start = now.strftime("%Y-%m-%d 00:00:00")
    week_start = (now - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # За сегодня (только выполненные)
        cursor.execute('SELECT COUNT(*), SUM(amount) FROM tasks WHERE status = "выполнено" AND created_at >= ?', (today_start,))
        today_count, today_sum = cursor.fetchone()
        today_sum = today_sum or 0

        # За неделю
        cursor.execute('SELECT COUNT(*), SUM(amount) FROM tasks WHERE status = "выполнено" AND created_at >= ?', (week_start,))
        week_count, week_sum = cursor.fetchone()
        week_sum = week_sum or 0

        # За всё время
        cursor.execute('SELECT COUNT(*), SUM(amount) FROM tasks WHERE status = "выполнено"')
        all_count, all_sum = cursor.fetchone()
        all_sum = all_sum or 0

        # Разбивка по площадкам (всё время, выполненные)
        cursor.execute('SELECT platform, COUNT(*), SUM(amount) FROM tasks WHERE status = "выполнено" GROUP BY platform')
        platforms = cursor.fetchall()

    return {
        "today": (today_count, today_sum),
        "week": (week_count, week_sum),
        "all": (all_count, all_sum),
        "platforms": platforms
    }