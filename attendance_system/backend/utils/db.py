# backend/utils/db.py
# ─────────────────────────────────────────────────────────────
# MySQL connection helper — credentials come from config.py
# ─────────────────────────────────────────────────────────────

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import mysql.connector
from mysql.connector import Error
from backend.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

DB_CONFIG = {
    "host":     DB_HOST,
    "port":     DB_PORT,
    "user":     DB_USER,
    "password": DB_PASSWORD,
    "database": DB_NAME,
}


def get_connection():
    """Return a live MySQL connection or raise a clear error."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        raise ConnectionError(f"[DB] Cannot connect to MySQL: {e}")


def query(sql: str, params: tuple = (), fetchone: bool = False):
    """
    Execute a SELECT query and return rows.
    fetchone=True  → returns a single dict or None
    fetchone=False → returns a list of dicts
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        return cursor.fetchone() if fetchone else cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def execute(sql: str, params: tuple = ()):
    """
    Execute an INSERT / UPDATE / DELETE query.
    Returns lastrowid.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()
