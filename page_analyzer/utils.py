from urllib.parse import urlparse
import validators


MAX_LEN_URL = 255


def normalize_url(input_url):
    url = urlparse(input_url)
    normalized_url = f'{url.scheme}://{url.hostname}'
    return normalized_url


def validate_url(input_url):
    return validators.url(input_url)


def check_url_length(input_url):
    return len(input_url) < MAX_LEN_URL


def prepare_flash_message(input_url):
    if not input_url:
        return 'URL обязателен'

    if not check_url_length(input_url):
        return 'URL превышает 255 символов'

    if not validate_url(input_url):
        return 'Некорректный URL'
