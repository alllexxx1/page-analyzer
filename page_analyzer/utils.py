from flask import render_template, flash
from urllib.parse import urlparse
import validators


def validate_and_normalize_url(input_url):
    if not input_url:
        flash('URL обязателен', 'error')
        return None

    if len(input_url) > 255:
        flash('URL превышает 255 символов', 'error')
        return None

    url = urlparse(input_url)
    normalized_url = f'{url.scheme}://{url.hostname}'
    validated_url = validators.url(normalized_url)

    if not validated_url:
        flash('Некорректный URL', 'error')
        return None

    return normalized_url


def render_template_with_error_flash(url, messages):
    return render_template(
        'index.html',
        url=url,
        messages=messages
    ), 422
