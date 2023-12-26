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
def new_url():
    url = ''
    return render_template(
        'index.html',
        url=url
    )


@app.route('/urls', methods=['POST'])
def post_url():
    input_url = request.form.get('url')

    flash_message = validate_url(input_url)
    if flash_message:
        error_message, error_type = flash_message[0]
        flash(error_message, error_type)
        messages = get_flashed_messages(with_categories=True)
        return render_template(
            'index.html',
            url=input_url,
            messages=messages
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
    result_data = db.get_urls_with_checks(conn)
    db.close_connection(conn)

    return render_template(
        'urls.html',
        urls=result_data
    )


@app.route('/urls/<int:id>', methods=['GET'])
def get_url(id):
    conn = db.create_connection(DATABASE_URL)
    url_data = db.get_url(conn, id)
    if not url_data:
        abort(404)

    checks = db.get_check(conn, id)
    db.close_connection(conn)

    messages = get_flashed_messages(with_categories=True)
    return render_template(
        'url.html',
        url=url_data,
        checks=checks,
        messages=messages
    )


@app.route('/urls/<id>/checks', methods=['POST'])
def check_url(id):
    conn = db.create_connection(DATABASE_URL)
    url = db.get_url(conn, id).name

    try:
        response = requests.get(url)
        status_code = response.status_code

        if status_code == 200:
            site_data = parser.get_seo_info(response)
            db.add_check(conn, id, status_code, site_data)
            flash('Страница успешно проверена', 'success')

        else:
            flash('Произошла ошибка при проверке', 'error')

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
