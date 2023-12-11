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
    prepare_flash_message,
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

    flash_message = prepare_flash_message(input_url)
    if flash_message:
        flash(flash_message, 'error')
        messages = get_flashed_messages(with_categories=True)
        return render_template(
            'index.html',
            url=input_url,
            messages=messages
        ), 422

    normalized_url = normalize_url(input_url)

    conn = db.create_connection(DATABASE_URL)
    url_data = db.get_url_by_name(conn, normalized_url)
    db.close_connection(conn)

    url_id = url_data.id if url_data else None
    if url_id:
        flash('Страница уже существует', 'info')
    else:
        conn = db.create_connection(DATABASE_URL)
        url_id = db.add_url(conn, normalized_url)
        db.close_connection(conn)

        flash('Страница успешно добавлена', 'success')
    return redirect(
        url_for('get_url', id=url_id), code=302
    )


@app.route('/urls', methods=['GET'])
def get_urls():
    conn = db.create_connection(DATABASE_URL)
    urls_data = db.get_urls(conn)
    db.close_connection(conn)

    conn = db.create_connection(DATABASE_URL)
    latest_checks = db.get_checks(conn)
    db.close_connection(conn)

    result_data = []
    for url in urls_data:
        latest_check_data = latest_checks.get(url.id, None)
        result_data.append({
            'id': url.id,
            'name': url.name,
            'check_created_at': latest_check_data['latest_created_at']
            if latest_check_data else None,
            'status_code': latest_check_data['status_code']
            if latest_check_data else None
        })
    return render_template(
        'urls.html',
        urls=result_data
    )


@app.route('/urls/<int:id>', methods=['GET'])
def get_url(id):
    conn = db.create_connection(DATABASE_URL)
    url_data = db.get_url(conn, id)
    db.close_connection(conn)
    if not url_data:
        abort(404)

    conn = db.create_connection(DATABASE_URL)
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
    db.close_connection(conn)

    try:
        response = requests.get(url)
        status_code = response.status_code

        if status_code == 200:
            site_data = parser.get_seo_info(response)
            conn = db.create_connection(DATABASE_URL)
            db.add_check(conn, id, status_code, site_data)
            db.close_connection(conn)
            flash('Страница успешно проверена', 'success')

        else:
            flash('Произошла ошибка при проверке', 'error')

    except requests.RequestException:
        flash('Произошла ошибка при проверке', 'error')

    return redirect(
        url_for('get_url', id=id), code=302
    )


@app.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500
