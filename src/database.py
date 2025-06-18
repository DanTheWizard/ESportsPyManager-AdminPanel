import sqlite3
from datetime import datetime

DB_PATH = "devices.db"  # This file will be created automatically

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id TEXT UNIQUE NOT NULL,
                nickname TEXT,
                registered_at TEXT,
                last_seen TEXT,
                tag TEXT
            )
        ''')
        conn.commit()

def register_device(machine_id, nickname, tag):
    now = datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO devices (machine_id, nickname, registered_at, last_seen, tag)
            VALUES (?, ?, ?, ?, ?)
        ''', (machine_id, nickname, now, now, tag))
        conn.commit()



def update_last_seen(machine_id):
    now = datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE devices SET last_seen = ? WHERE machine_id = ?
        ''', (now, machine_id))
        conn.commit()

def get_all_devices():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT machine_id, nickname, registered_at, last_seen FROM devices')
        return cursor.fetchall()

def get_registered_devices():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT machine_id, nickname, registered_at, last_seen, tag
            FROM devices
            WHERE nickname IS NOT NULL AND nickname != ''
            ORDER BY LOWER(nickname) ASC
        ''')
        return cursor.fetchall()

def get_unregistered_devices():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT machine_id, nickname, registered_at, last_seen
            FROM devices
            WHERE nickname IS NULL OR nickname = ''
            ORDER BY LOWER(machine_id) ASC
        ''')
        return cursor.fetchall()


def remove_device(machine_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM devices WHERE machine_id = ?', (machine_id,))
        conn.commit()
