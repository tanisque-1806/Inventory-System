from contextlib import contextmanager
from decimal import Decimal

import mysql.connector

from .config import Config


def get_connection():
    return mysql.connector.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
    )


@contextmanager
def db_cursor(dictionary=True):
    conn = get_connection()
    cursor = conn.cursor(dictionary=dictionary)
    try:
        yield conn, cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def fetch_all(query, params=None):
    with db_cursor() as (_, cursor):
        cursor.execute(query, params or ())
        return normalize_rows(cursor.fetchall())


def fetch_one(query, params=None):
    with db_cursor() as (_, cursor):
        cursor.execute(query, params or ())
        row = cursor.fetchone()
        return normalize_row(row)


def execute(query, params=None):
    with db_cursor() as (_, cursor):
        cursor.execute(query, params or ())
        return cursor.lastrowid


def call_procedure(name, args):
    with db_cursor(dictionary=False) as (conn, cursor):
        result = cursor.callproc(name, args)
        payload = []
        for stored_result in cursor.stored_results():
            rows = stored_result.fetchall()
            columns = stored_result.column_names
            payload.extend([dict(zip(columns, row)) for row in rows])
        conn.commit()
        return result, normalize_rows(payload)


def normalize_rows(rows):
    return [normalize_row(row) for row in rows]


def normalize_row(row):
    if not row:
        return row
    normalized = {}
    for key, value in row.items():
        if isinstance(value, Decimal):
            normalized[key] = float(value)
        else:
            normalized[key] = value
    return normalized
