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

    # Translation payloads may localize human-readable summaries, but schema enums
    # must remain language-neutral or the localized collection fails validation.
    base_history = base.get('change_history') or []
    localized_history = result.get('change_history') or []
    for index, item in enumerate(localized_history):
        if index < len(base_history) and isinstance(item, dict):
            item['type'] = base_history[index].get('type', 'data-review')
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


def localize_tools(tools, locale, path=DATABASE_PATH):
    """Localize a collection with one SQL query instead of one query per tool."""
    if not tools or locale == DEFAULT_LOCALE:
        return tools
    tool_ids = [tool.get("id") for tool in tools if tool.get("id") is not None]
    if not tool_ids:
        return tools
    placeholders = ",".join("?" for _ in tool_ids)
    with connect_database(path) as connection:
        rows = connection.execute(
            f"SELECT * FROM tool_translations WHERE locale=? AND tool_id IN ({placeholders})",
            [locale, *tool_ids],
        ).fetchall()
    translations = {row["tool_id"]: dict(row) for row in rows}
    return [_merge_payload(tool, translations.get(tool.get("id"))) for tool in tools]


def localize_articles(articles, locale, path=DATABASE_PATH):
    """Localize article collections with a single translation lookup."""
    if not articles or locale == DEFAULT_LOCALE:
        return articles
    article_ids = [article.get("id") for article in articles if article.get("id") is not None]
    if not article_ids:
        return articles
    placeholders = ",".join("?" for _ in article_ids)
    with connect_database(path) as connection:
        rows = connection.execute(
            f"SELECT * FROM article_translations WHERE locale=? AND article_id IN ({placeholders})",
            [locale, *article_ids],
        ).fetchall()
    translations = {row["article_id"]: dict(row) for row in rows}
    localized = []
    for article in articles:
        data = translations.get(article.get("id"))
        if not data:
            result = dict(article)
            result["_translation_fallback"] = True
            localized.append(result)
            continue
        result = dict(article)
        try:
            result.update(json.loads(data.get("payload_json") or "{}"))
        except json.JSONDecodeError:
            pass
        if data.get("title"):
            result["title"] = data["title"]
        if data.get("description"):
            result["description"] = data["description"]
        localized.append(result)
    return localized
