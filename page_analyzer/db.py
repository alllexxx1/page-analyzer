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
        url = cur.fetchone()
    return url


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


def get_urls_with_checks(conn):
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        cur.execute('SELECT id, name FROM urls ORDER BY id DESC')
        urls = cur.fetchall()

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

    urls_with_checks = []
    for url in urls:
        latest_check_data = latest_checks.get(url.id, None)
        urls_with_checks.append({
            'id': url.id,
            'name': url.name,
            'check_created_at': latest_check_data['latest_created_at']
            if latest_check_data else None,
            'status_code': latest_check_data['status_code']
            if latest_check_data else None
        })
    return urls_with_checks


def get_url(conn, id):
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        cur.execute('SELECT * FROM urls WHERE id=%s', (id,))
        url = cur.fetchone()
    return url


def get_checks(conn, id):
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
