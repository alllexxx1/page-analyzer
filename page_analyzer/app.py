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
        return render_template(
            'main_page.html',
            url=input_url,
            messages=messages
        ), 422

    url = urlparse(input_url)
    normalized_url = f'{url.scheme}://{url.hostname}'
    validated_url = validators.url(normalized_url)
    if not validated_url:
        flash('Некорректный URL', 'error')
        messages = get_flashed_messages(with_categories=True)
        return render_template(
            'main_page.html',
            url=input_url,
            messages=messages
        ), 422

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
        cur.execute('SELECT id FROM urls WHERE name=%s', (normalized_url,))
        id_ = cur.fetchone()[0]
    conn.commit()
    conn.close()

    flash('Страница успешно добавлена', 'success')
    return redirect(
        url_for('get_url', id=id_), code=302
    )


@app.route('/urls', methods=['GET'])
def get_urls():
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        cur.execute('SELECT * FROM urls ORDER BY id DESC')
        urls_data = cur.fetchall()
    conn.close()

    return render_template(
        'index.html',
        urls=urls_data
    )


@app.route('/urls/<id>', methods=['GET'])
def get_url(id):
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        cur.execute('SELECT * FROM urls WHERE id=%s', (id,))
        url_data = cur.fetchone()
    conn.close()

    messages = get_flashed_messages(with_categories=True)
    return render_template(
        'show.html',
        url=url_data,
        messages=messages
    )
