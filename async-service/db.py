import sqlite3
from datetime import datetime
import time

DB_NAME = "tasks.db"

def connect_with_retry(retries=5, delay=2):
    for attempt in range(retries):
        try:
            conn = sqlite3.connect(DB_NAME)
            return conn
        except sqlite3.OperationalError as e:
            print(f"[!] Не удалось подключиться к базе данных: {e}, попытка {attempt + 1}")
            time.sleep(delay)
    raise Exception("❌ Не удалось подключиться к базе данных после нескольких попыток")

def init_db():
    conn = connect_with_retry()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            equipment_id TEXT,
            parameters TEXT,
            timestamp TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

def create_task(task_id, equipment_id, parameters):
    conn = connect_with_retry()
    c = conn.cursor()
    c.execute('INSERT INTO tasks VALUES (?, ?, ?, ?, ?)', (
        task_id,
        equipment_id,
        parameters,
        datetime.now().isoformat(),
        "running"
    ))
    conn.commit()
    conn.close()

def update_task_status(task_id, status):
    conn = connect_with_retry()
    c = conn.cursor()
    c.execute('UPDATE tasks SET status = ? WHERE task_id = ?', (status, task_id))
    conn.commit()
    conn.close()

def get_task(task_id):
    conn = connect_with_retry()
    c = conn.cursor()
    c.execute('SELECT status FROM tasks WHERE task_id = ?', (task_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None
