import json
from database import DATABASE_PATH, connect_database
from i18n import DEFAULT_LOCALE


def _merge_payload(base, translated):
    if not translated:
        return base
    result = dict(base)
    payload = translated.get('payload_json')
    if payload:
        try:
            result.update(json.loads(payload))
        except (TypeError, json.JSONDecodeError):
            pass
    for key in ('name', 'description', 'subcategory'):
        if translated.get(key):
            result[key] = translated[key]
    if translated.get('pricing_summary') or translated.get('pricing_notes'):
        details = dict(result.get('pricing_details') or {})
        if translated.get('pricing_summary'):
            details['summary'] = translated['pricing_summary']
        if translated.get('pricing_notes'):
            details['notes'] = translated['pricing_notes']
        result['pricing_details'] = details
    return result


def localize_tool(tool, locale, path=DATABASE_PATH):
    if not tool or locale == DEFAULT_LOCALE:
        return tool
    with connect_database(path) as connection:
        row = connection.execute(
            'SELECT * FROM tool_translations WHERE tool_id=? AND locale=?',
            (tool.get('id'), locale),
        ).fetchone()
    return _merge_payload(tool, dict(row) if row else None)


def localize_article(article, locale, path=DATABASE_PATH):
    if not article or locale == DEFAULT_LOCALE:
        return article
    with connect_database(path) as connection:
        row = connection.execute(
            'SELECT * FROM article_translations WHERE article_id=? AND locale=?',
            (article.get('id'), locale),
        ).fetchone()
    if not row:
        result = dict(article)
        result['_translation_fallback'] = True
        return result
    result = dict(article)
    data = dict(row)
    try:
        result.update(json.loads(data.get('payload_json') or '{}'))
    except json.JSONDecodeError:
        pass
    if data.get('title'):
        result['title'] = data['title']
    if data.get('description'):
        result['description'] = data['description']
    return result
