import psycopg2
from psycopg2.extras import NamedTupleCursor


def create_connection(database_url):
    conn = psycopg2.connect(database_url)
    return conn


def close_connection(conn):
    conn.close()


def get_url_by_name(conn, normalized_url):
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        cur.execute('SELECT name, id FROM urls WHERE name=%s',
                    (normalized_url,))
        url_data = cur.fetchone()
    return url_data


def add_url(conn, normalized_url):
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        cur.execute("""
            INSERT INTO urls (name)
            VALUES (%s) RETURNING id;
            """,
                    (normalized_url,))
        url_id = cur.fetchone().id
    conn.commit()
    return url_id


def get_urls(conn):
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        cur.execute('SELECT id, name FROM urls ORDER BY id DESC')
        urls_data = cur.fetchall()
    return urls_data


def get_checks(conn):
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
    return latest_checks


def get_url(conn, id):
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        cur.execute('SELECT * FROM urls WHERE id=%s', (id,))
        url_data = cur.fetchone()
    return url_data


def get_check(conn, id):
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        cur.execute('''
            SELECT *
            FROM url_checks WHERE url_id=%s
            ORDER BY id DESC''', (id,))
        checks = cur.fetchall()
    return checks


def add_check(conn, id, status_code, site_data):
    with conn.cursor() as cur:
        cur.execute("""
               INSERT INTO url_checks (url_id, status_code, h1,
               title, description)
               VALUES (%s, %s, %s, %s, %s);
               """,
                    (id, status_code,
                     site_data['h1'],
                     site_data['title'],
                     site_data['description']))
    conn.commit()
