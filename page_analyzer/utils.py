from urllib.parse import urlparse
import validators


MAX_LEN_URL = 255


def normalize_url(input_url):
    url = urlparse(input_url)
    normalized_url = f'{url.scheme}://{url.hostname}'
    return normalized_url


def verify_url(input_url):
    return validators.url(input_url)


def check_url_length(input_url):
    return len(input_url) < MAX_LEN_URL


def validate_url(input_url):
    errors = []
    if not input_url:
        errors.append(('URL обязателен', 'error'))
    if not check_url_length(input_url):
        errors.append(('URL превышает 255 символов', 'error'))
    if not verify_url(input_url):
        errors.append(('Некорректный URL', 'error'))
    return errors
