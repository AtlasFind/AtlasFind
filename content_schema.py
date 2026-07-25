"""Validation rules for AtlasFind editorial content."""

from __future__ import annotations

from datetime import date
from typing import Any

ALLOWED_CONTENT_TYPES = {
    "guide",
    "best-tools",
    "alternatives",
    "comparison",
    "category-guide",
}

REQUIRED_FIELDS = {
    "slug",
    "title",
    "description",
    "content_type",
    "category",
    "published_at",
    "updated_at",
    "author",
    "sections",
    "faq",
    "related_tool_slugs",
    "related_article_slugs",
}


def _valid_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def validate_articles(articles: Any, tool_slugs: set[str] | None = None) -> list[str]:
    errors: list[str] = []
    tool_slugs = tool_slugs or set()

    if not isinstance(articles, list):
        return ["articles.json must contain a JSON list."]

    seen_slugs: set[str] = set()
    article_slugs = {
        article.get("slug")
        for article in articles
        if isinstance(article, dict) and isinstance(article.get("slug"), str)
    }

    for index, article in enumerate(articles, start=1):
        prefix = f"Article #{index}"
        if not isinstance(article, dict):
            errors.append(f"{prefix} must be an object.")
            continue

        missing = sorted(REQUIRED_FIELDS - article.keys())
        if missing:
            errors.append(f"{prefix} is missing fields: {', '.join(missing)}.")

        slug = article.get("slug")
        if not isinstance(slug, str) or not slug.strip():
            errors.append(f"{prefix} has an invalid slug.")
        elif slug in seen_slugs:
            errors.append(f"Duplicate article slug: {slug}.")
        else:
            seen_slugs.add(slug)

        for field in ("title", "description", "category", "author"):
            if not isinstance(article.get(field), str) or not article.get(field, "").strip():
                errors.append(f"{prefix} has an invalid {field}.")

        if article.get("content_type") not in ALLOWED_CONTENT_TYPES:
            errors.append(f"{prefix} has an unsupported content_type.")

        for field in ("published_at", "updated_at"):
            if not _valid_date(article.get(field)):
                errors.append(f"{prefix} has an invalid {field}; use YYYY-MM-DD.")

        sections = article.get("sections")
        section_ids: set[str] = set()
        if not isinstance(sections, list) or not sections:
            errors.append(f"{prefix} must include at least one section.")
        else:
            for section_index, section in enumerate(sections, start=1):
                section_prefix = f"{prefix} section #{section_index}"
                if not isinstance(section, dict):
                    errors.append(f"{section_prefix} must be an object.")
                    continue
                section_id = section.get("id")
                if not isinstance(section_id, str) or not section_id.strip():
                    errors.append(f"{section_prefix} has an invalid id.")
                elif section_id in section_ids:
                    errors.append(f"{prefix} has duplicate section id: {section_id}.")
                else:
                    section_ids.add(section_id)
                if not isinstance(section.get("title"), str) or not section.get("title", "").strip():
                    errors.append(f"{section_prefix} has an invalid title.")
                paragraphs = section.get("paragraphs", [])
                if not isinstance(paragraphs, list) or not all(isinstance(item, str) and item.strip() for item in paragraphs):
                    errors.append(f"{section_prefix} paragraphs must be a list of non-empty strings.")
                tool_refs = section.get("tool_slugs", [])
                if not isinstance(tool_refs, list):
                    errors.append(f"{section_prefix} tool_slugs must be a list.")
                else:
                    for tool_slug in tool_refs:
                        if tool_slug not in tool_slugs:
                            errors.append(f"{section_prefix} references unknown tool slug: {tool_slug}.")

        faq = article.get("faq")
        if not isinstance(faq, list):
            errors.append(f"{prefix} faq must be a list.")
        else:
            for faq_index, item in enumerate(faq, start=1):
                if not isinstance(item, dict) or not isinstance(item.get("question"), str) or not isinstance(item.get("answer"), str):
                    errors.append(f"{prefix} FAQ #{faq_index} must include question and answer strings.")

        for tool_slug in article.get("related_tool_slugs", []) if isinstance(article.get("related_tool_slugs"), list) else []:
            if tool_slug not in tool_slugs:
                errors.append(f"{prefix} references unknown related tool slug: {tool_slug}.")

        related_articles = article.get("related_article_slugs")
        if not isinstance(related_articles, list):
            errors.append(f"{prefix} related_article_slugs must be a list.")
        else:
            for related_slug in related_articles:
                if related_slug == slug:
                    errors.append(f"{prefix} cannot reference itself as a related article.")
                elif related_slug not in article_slugs:
                    errors.append(f"{prefix} references unknown related article slug: {related_slug}.")

    return errors
