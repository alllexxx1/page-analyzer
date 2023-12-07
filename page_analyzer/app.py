from flask import (
    Flask, render_template, redirect,
    request, url_for, flash, get_flashed_messages
)
import os
from dotenv import load_dotenv
import requests
from page_analyzer import db
from page_analyzer import parser
from page_analyzer.utils import (validate_and_normalize_url,
                                 render_template_with_error_flash)


app = Flask(__name__)

load_dotenv()
app.secret_key = os.environ.get('SECRET_KEY')


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

    normalized_url = validate_and_normalize_url(input_url)

    if normalized_url is None:
        messages = get_flashed_messages(with_categories=True)
        return render_template_with_error_flash(input_url, messages)

    url_id = db.get_url_id_by_name(normalized_url)

    if url_id:
        flash('Страница уже существует', 'info')
    else:
        db.add_url(normalized_url)
        url_id = db.get_url_id_by_name(normalized_url)
        flash('Страница успешно добавлена', 'success')
    return redirect(
        url_for('get_url', id=url_id), code=302
    )


@app.route('/urls', methods=['GET'])
def get_urls():
    urls_data = db.get_urls_by_desc()
    latest_checks = db.get_checks_by_desc()

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
    url_id = db.get_url_id_by_id(id)
    if not url_id:
        return render_template('errors/404.html'), 404

    url_data = db.get_url_data(id)
    checks = db.get_checks_data_by_desc(id)

    messages = get_flashed_messages(with_categories=True)
    return render_template(
        'url.html',
        url=url_data,
        checks=checks,
        messages=messages
    )


@app.route('/urls/<id>/checks', methods=['POST'])
def check_url(id):
    url = db.get_url_name_by_id(id)

    try:
        response = requests.get(url)
        status_code = response.status_code

        if status_code == 200:
            site_data = parser.get_seo_info(response)
            db.add_check(id, status_code, site_data)
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
