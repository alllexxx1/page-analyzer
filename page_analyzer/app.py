from flask import (
    Flask,
    render_template,
    redirect,
    request,
    url_for,
    flash,
    get_flashed_messages
)
import psycopg2
from psycopg2.extras import NamedTupleCursor
import os
from dotenv import load_dotenv
from urllib.parse import urlparse
import validators
from datetime import date
import requests


app = Flask(__name__)

load_dotenv()
app.secret_key = os.environ.get('SECRET_KEY')

DATABASE_URL = os.getenv('DATABASE_URL')


@app.route('/', methods=['GET'])
def new_url():
    url = ''
    return render_template(
        'main_page.html',
        url=url
    )


@app.route('/urls', methods=['POST'])
def post_url():
    input_url = request.form.get('url')

    if not input_url:
        flash('URL обязателен', 'error')
        messages = get_flashed_messages(with_categories=True)
        return render_template_with_error_flash(input_url, messages)

    if len(input_url) > 255:
        flash('URL превышает 255 символов', 'error')
        messages = get_flashed_messages(with_categories=True)
        return render_template_with_error_flash(input_url, messages)

    url = urlparse(input_url)
    normalized_url = f'{url.scheme}://{url.hostname}'
    validated_url = validators.url(normalized_url)
    if not validated_url:
        flash('Некорректный URL', 'error')
        messages = get_flashed_messages(with_categories=True)
        return render_template_with_error_flash(input_url, messages)

    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        cur.execute('SELECT name, id FROM urls WHERE name=%s',
                    (normalized_url,))
        url_data = cur.fetchone()
    conn.close()

    if url_data:
        id_ = url_data.id
        flash('Страница уже существует', 'info')
        return redirect(
            url_for('get_url', id=id_), code=302
        )

    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO urls (name, created_at)
            VALUES (%s, %s);
            """,
                    (normalized_url, date.today()))
    conn.commit()
    conn.close()

    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        cur.execute('SELECT id FROM urls WHERE name=%s', (normalized_url,))
        id_ = cur.fetchone().id
    conn.close()

    flash('Страница успешно добавлена', 'success')
    return redirect(
        url_for('get_url', id=id_), code=302
    )


@app.route('/urls', methods=['GET'])
def get_urls():
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        cur.execute('''
            SELECT DISTINCT ON (urls.id)
                urls.id,
                urls.name,
                url_checks.created_at as check_created_at,
                url_checks.status_code
            FROM urls
            LEFT JOIN url_checks ON urls.id = url_checks.url_id
            ORDER BY urls.id DESC, check_created_at DESC
        ''')
        urls_data = cur.fetchall()
    conn.close()

    return render_template(
        'index.html',
        urls=urls_data
    )


# @app.route('/urls', methods=['GET'])
# def get_urls():
#     conn = psycopg2.connect(DATABASE_URL)
#     with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
#         cur.execute('SELECT * FROM urls ORDER BY id DESC')
#         urls_data = cur.fetchall()
#     conn.close()
#
#     return render_template(
#         'index.html',
#         urls=urls_data
#     )


@app.route('/urls/<id>', methods=['GET'])
def get_url(id):
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        cur.execute('SELECT * FROM urls WHERE id=%s', (id,))
        url_data = cur.fetchone()
    conn.close()

    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        cur.execute('''
            SELECT id, status_code, created_at
            FROM url_checks WHERE url_id=%s
            ORDER BY id DESC''', (id,))
        checks = cur.fetchall()
    conn.close()

    messages = get_flashed_messages(with_categories=True)
    return render_template(
        'show.html',
        url=url_data,
        checks=checks,
        messages=messages
    )


@app.route('/urls/<id>/checks', methods=['POST'])
def check_url(id):
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        cur.execute('SELECT name FROM urls WHERE id=%s', (id,))
        url = cur.fetchone().name
    conn.close()

    try:
        response = requests.get(url)
        status_code = response.status_code

        if status_code == 200:
            conn = psycopg2.connect(DATABASE_URL)
            with conn.cursor() as cur:
                cur.execute("""
                       INSERT INTO url_checks (status_code, url_id, created_at)
                       VALUES (%s, %s, %s);
                       """,
                            (status_code, id, date.today()))
            conn.commit()
            conn.close()
            flash('Страница успешно проверена', 'success')

        else:
            flash('Произошла ошибка при проверке', 'error')

    except requests.RequestException:
        flash('Произошла ошибка при проверке', 'error')

    # conn = psycopg2.connect(DATABASE_URL)
    # with conn.cursor() as cur:
    #     cur.execute("""
    #            INSERT INTO url_checks (url_id, created_at)
    #            VALUES (%s, %s);
    #            """,
    #                 (id, date.today()))
    # conn.commit()
    # conn.close()
    #
    # flash('Страница успешно проверена', 'success')
    return redirect(
        url_for('get_url', id=id), code=302
    )


@app.errorhandler(404)
def not_found(error):
    return render_template('not_found.html'), 404


def render_template_with_error_flash(url, messages):
    return render_template(
        'main_page.html',
        url=url,
        messages=messages
    ), 422
