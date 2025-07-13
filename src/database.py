import sqlite3
from datetime import datetime, timedelta
from config import OFFLINE_DEVICE_TIMEOUT
import os

FOLDER_PATH = r"db"
os.makedirs(FOLDER_PATH, exist_ok=True)
DB_PATH = f"{FOLDER_PATH}\\devices.db"  # This file will be created automatically

def init_db():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    machine_id TEXT UNIQUE NOT NULL,
                    nickname TEXT,
                    registered_at TEXT,
                    tag TEXT
                )
            ''')
            conn.commit()
            print("[DB] Device Database initialized successfully.")
    except Exception as e:
        print(f"[DB] Device Database Initialization failed: {e}")


def init_device_status_table():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS device_status (
                    machine_id TEXT PRIMARY KEY,
                    hostname TEXT,
                    cpu TEXT,
                    ram TEXT,
                    user TEXT,
                    app TEXT,
                    version TEXT,
                    last_seen TEXT
                )
            ''')
            conn.commit()
            print("[DB] Device Status initialized successfully.")
    except Exception as e:
        print(f"[DB] Device Status Initialization failed: {e}")


def register_device(machine_id, nickname, tag):
    now = datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO devices (machine_id, nickname, registered_at, tag)
            VALUES (?, ?, ?, ?)
        ''', (machine_id, nickname, now, tag))
        conn.commit()



def update_last_seen(machine_id, iso_timestamp=None):
    now = iso_timestamp or datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE device_status SET last_seen = ? WHERE machine_id = ?
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
            SELECT machine_id, nickname, registered_at, tag
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




########################################################################################################################

def upsert_device_status(machine_id, data: dict):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO device_status (machine_id, hostname, cpu, ram, user, app, version, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(machine_id) DO UPDATE SET
                hostname = excluded.hostname,
                cpu = excluded.cpu,
                ram = excluded.ram,
                user = excluded.user,
                app = excluded.app,
                version = excluded.version,
                last_seen = excluded.last_seen
        ''', (
            machine_id,
            data.get("hostname"),
            data.get("cpu"),
            data.get("ram"),
            data.get("user"),
            data.get("app"),
            data.get("version"),
            now
        ))
        conn.commit()

def get_online_devices():
    cutoff = datetime.now() - timedelta(seconds=OFFLINE_DEVICE_TIMEOUT)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT machine_id FROM device_status
            WHERE last_seen >= ?
        ''', (cutoff.isoformat(),))
        return {row[0] for row in cursor.fetchall()}

def get_all_device_status():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM device_status')
        return cursor.fetchall()


def get_last_seen(machine_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT last_seen FROM device_status WHERE machine_id = ?', (machine_id,))
        row = cursor.fetchone()
        return row[0] if row else None
