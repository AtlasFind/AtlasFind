CREATE TABLE IF NOT EXISTS tool_translations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL REFERENCES tools(id) ON DELETE CASCADE,
    locale TEXT NOT NULL,
    name TEXT,
    description TEXT,
    subcategory TEXT,
    pricing_summary TEXT,
    pricing_notes TEXT,
    payload_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE(tool_id, locale)
);
CREATE INDEX IF NOT EXISTS idx_tool_translations_locale ON tool_translations(locale);

CREATE TABLE IF NOT EXISTS article_translations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    locale TEXT NOT NULL,
    title TEXT,
    description TEXT,
    payload_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE(article_id, locale)
);
CREATE INDEX IF NOT EXISTS idx_article_translations_locale ON article_translations(locale);

INSERT OR IGNORE INTO tool_translations(tool_id, locale, name, description, subcategory, pricing_summary, pricing_notes, payload_json)
SELECT id, 'en', name, description, json_extract(payload_json, '$.subcategory'),
       json_extract(payload_json, '$.pricing_details.summary'), json_extract(payload_json, '$.pricing_details.notes'), payload_json
FROM tools;

INSERT OR IGNORE INTO article_translations(article_id, locale, title, description, payload_json)
SELECT id, 'en', title, description, payload_json FROM articles;
