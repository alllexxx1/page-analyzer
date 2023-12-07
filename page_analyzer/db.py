import os
import psycopg2
from psycopg2.extras import NamedTupleCursor
from dotenv import load_dotenv
from datetime import date


load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


def get_url_id_by_name(normalized_url):
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        cur.execute('SELECT name, id FROM urls WHERE name=%s',
                    (normalized_url,))
        url_data = cur.fetchone()
        url_id = url_data.id if url_data else None
    conn.close()
    return url_id


def add_url(normalized_url):
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO urls (name, created_at)
            VALUES (%s, %s);
            """,
                    (normalized_url, date.today()))
    conn.commit()
    conn.close()


def get_urls_by_desc():
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        cur.execute('SELECT id, name FROM urls ORDER BY id DESC')
        urls_data = cur.fetchall()
    conn.close()
    return urls_data


def get_checks_by_desc():
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        latest_checks = {}
        cur.execute('''
            SELECT url_id, MAX(created_at) AS latest_created_at, status_code
            FROM url_checks
            GROUP BY url_id, status_code
            ORDER BY url_id DESC''')
        for row in cur.fetchall():
            latest_checks[row.url_id] = {
                'latest_created_at': row.latest_created_at,
                'status_code': row.status_code
            }
    conn.close()
    return latest_checks


def get_url_id_by_id(id):
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor() as cur:
        cur.execute('SELECT id FROM urls WHERE id=%s', (id,))
        url_id = cur.fetchone()
    conn.close()
    return url_id


def get_url_data(id):
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        cur.execute('SELECT * FROM urls WHERE id=%s', (id,))
        url_data = cur.fetchone()
    conn.close()
    return url_data


def get_checks_data_by_desc(id):
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        cur.execute('''
            SELECT *
            FROM url_checks WHERE url_id=%s
            ORDER BY id DESC''', (id,))
        checks = cur.fetchall()
    conn.close()
    return checks


def get_url_name_by_id(id):
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        cur.execute('SELECT name FROM urls WHERE id=%s', (id,))
        url = cur.fetchone().name
    conn.close()
    return url


def add_check(id, status_code, site_data):
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor() as cur:
        cur.execute("""
               INSERT INTO url_checks (url_id, status_code, h1,
               title, description, created_at)
               VALUES (%s, %s, %s, %s, %s, %s);
               """,
                    (id, status_code,
                     site_data['h1'],
                     site_data['title'],
                     site_data['description'],
                     date.today()))
    conn.commit()
    conn.close()
