from flask import (
    Flask, render_template, redirect,
    request, url_for, flash,
    get_flashed_messages, abort
)
import os
from dotenv import load_dotenv
import requests
from page_analyzer import db
from page_analyzer import parser
from page_analyzer.utils import (
    validate_url,
    normalize_url
)


app = Flask(__name__)

load_dotenv()
app.secret_key = os.environ.get('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')


@app.route('/', methods=['GET'])
def index():
    return render_template(
        'index.html',
        url=''
    )


@app.route('/urls', methods=['POST'])
def post_url():
    input_url = request.form.get('url')

    messages = validate_url(input_url)
    if messages:
        for message, message_type in messages:
            flash(message, message_type)
        return render_template(
            'index.html',
            url=input_url,
            messages=get_flashed_messages(with_categories=True)
        ), 422

    normalized_url = normalize_url(input_url)

    conn = db.create_connection(DATABASE_URL)
    url = db.get_url_by_name(conn, normalized_url)

    url_id = url.id if url else None
    if url_id:
        flash('Страница уже существует', 'info')
    else:
        url_id = db.add_url(conn, normalized_url)
        flash('Страница успешно добавлена', 'success')

    db.close_connection(conn)
    return redirect(
        url_for('get_url', id=url_id), code=302
    )


@app.route('/urls', methods=['GET'])
def get_urls():
    conn = db.create_connection(DATABASE_URL)
    urls_with_checks = db.get_urls_with_checks(conn)
    db.close_connection(conn)

    return render_template(
        'urls.html',
        urls=urls_with_checks
    )


@app.route('/urls/<int:id>', methods=['GET'])
def get_url(id):
    conn = db.create_connection(DATABASE_URL)
    url = db.get_url(conn, id)
    if not url:
        abort(404)

    checks = db.get_checks(conn, id)
    db.close_connection(conn)

    return render_template(
        'url.html',
        url=url,
        checks=checks,
        messages=get_flashed_messages(with_categories=True)
    )


@app.route('/urls/<id>/checks', methods=['POST'])
def check_url(id):
    conn = db.create_connection(DATABASE_URL)
    url = db.get_url(conn, id)

    try:
        response = requests.get(url.name)
        response.raise_for_status()
        status_code = response.status_code
        site_data = parser.get_seo_info(response)
        db.add_check(conn, id, status_code, site_data)
        flash('Страница успешно проверена', 'success')

    except requests.RequestException:
        flash('Произошла ошибка при проверке', 'error')

    db.close_connection(conn)
    return redirect(
        url_for('get_url', id=id), code=302
    )


@app.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500
