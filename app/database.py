import sqlite3

# Подключение к БД
db_conn = sqlite3.connect("chat.db", check_same_thread=False)
db_conn.execute("PRAGMA journal_mode=WAL")   # Безопаснее при конкурентном доступе
db_conn.execute("PRAGMA foreign_keys=ON")

def init_db():
    cursor = db_conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username    TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS offline_messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sender      TEXT NOT NULL,
            receiver    TEXT NOT NULL,
            ciphertext  TEXT NOT NULL
        )
    ''')
    db_conn.commit()