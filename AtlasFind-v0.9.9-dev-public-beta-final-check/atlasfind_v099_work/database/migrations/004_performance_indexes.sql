CREATE INDEX IF NOT EXISTS idx_tools_status_rating ON tools(status, rating DESC);
CREATE INDEX IF NOT EXISTS idx_tools_status_category ON tools(status, category_id);
CREATE INDEX IF NOT EXISTS idx_tools_status_updated ON tools(status, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_status_published ON articles(status, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_tool_translations_locale_tool ON tool_translations(locale, tool_id);
CREATE INDEX IF NOT EXISTS idx_article_translations_locale_article ON article_translations(locale, article_id);
