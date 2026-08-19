import json
from functools import lru_cache
from pathlib import Path
try:
    from flask import g, has_request_context, request
except ModuleNotFoundError:  # Validation scripts can run before Flask is installed.
    g = None
    has_request_context = None
    request = None

BASE_DIR = Path(__file__).resolve().parent
TRANSLATIONS_DIR = BASE_DIR / 'translations'
DEFAULT_LOCALE = 'en'
SUPPORTED_LOCALES = {
    'en': {'name': 'English', 'short': 'EN'},
    'tr': {'name': 'Türkçe', 'short': 'TR'},
}

@lru_cache(maxsize=None)
def load_translations(locale):
    locale = locale if locale in SUPPORTED_LOCALES else DEFAULT_LOCALE
    path = TRANSLATIONS_DIR / f'{locale}.json'
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


def get_locale():
    if g is None or request is None or has_request_context is None or not has_request_context():
        return DEFAULT_LOCALE
    locale = getattr(g, 'locale', None)
    if locale in SUPPORTED_LOCALES:
        return locale
    view_args = getattr(request, 'view_args', None) or {}
    candidate = view_args.get('locale')
    return candidate if candidate in SUPPORTED_LOCALES else DEFAULT_LOCALE


def translate(key, **values):
    locale = get_locale()
    text = load_translations(locale).get(key)
    if text is None:
        text = load_translations(DEFAULT_LOCALE).get(key, key)
    try:
        return text.format(**values)
    except (KeyError, ValueError):
        return text


def localized_path(path='/', locale=None):
    if path is None:
        return None
    locale = locale or get_locale()
    if not path.startswith('/'):
        path = '/' + path
    if path == '/':
        return f'/{locale}/'
    if path.startswith(('/static/', '/admin/', '/api/', '/robots.txt', '/sitemap.xml')):
        return path
    parts = path.lstrip('/').split('/', 1)
    if parts[0] in SUPPORTED_LOCALES:
        path = '/' + (parts[1] if len(parts) > 1 else '')
    return f'/{locale}{path}'


def alternate_urls(path):
    return {locale: localized_path(path, locale) for locale in SUPPORTED_LOCALES}
