import json
import os
from urllib.parse import urljoin

SITE_NAME = "AtlasFind"
SITE_URL = os.environ.get("ATLASFIND_SITE_URL", "https://atlasfind.com").rstrip("/")
DEFAULT_SOCIAL_IMAGE = os.environ.get("ATLASFIND_SOCIAL_IMAGE", f"{SITE_URL}/static/images/atlasfind-social.svg")


def absolute_url(path="/"):
    if not path.startswith("/"):
        path = "/" + path
    return urljoin(SITE_URL + "/", path.lstrip("/"))


def page_seo(title, description, path="/", page_type="website", image=None, robots="index,follow"):
    clean_title = title if title.endswith(SITE_NAME) else f"{title} | {SITE_NAME}"
    return {
        "title": clean_title,
        "description": description.strip(),
        "canonical": absolute_url(path),
        "type": page_type,
        "image": image or DEFAULT_SOCIAL_IMAGE,
        "robots": robots,
    }


def breadcrumbs(items):
    result = []
    for position, item in enumerate(items, start=1):
        result.append({"name": item[0], "url": absolute_url(item[1]), "position": position})
    return result


def breadcrumb_schema(items):
    if not items:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": item["position"], "name": item["name"], "item": item["url"]}
            for item in items
        ],
    }


def website_schema():
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE_NAME,
        "url": SITE_URL,
        "potentialAction": {
            "@type": "SearchAction",
            "target": absolute_url("/?q={search_term_string}"),
            "query-input": "required name=search_term_string",
        },
    }


def software_schema(tool):
    data = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": tool.get("name"),
        "description": tool.get("description"),
        "applicationCategory": tool.get("category") or "SoftwareApplication",
        "operatingSystem": ", ".join(tool.get("platforms") or []),
        "url": absolute_url(f"/tools/{tool.get('slug','')}")
    }
    rating = tool.get("rating")
    if isinstance(rating, (int, float)):
        data["aggregateRating"] = {"@type": "AggregateRating", "ratingValue": rating, "bestRating": 5, "ratingCount": 1}
    website = tool.get("website")
    if website:
        data["sameAs"] = website
    return data


def article_schema(article):
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": article.get("title"),
        "description": article.get("description"),
        "datePublished": article.get("published_at"),
        "dateModified": article.get("updated_at"),
        "author": {"@type": "Organization", "name": article.get("author") or "AtlasFind Editors"},
        "publisher": {"@type": "Organization", "name": SITE_NAME},
        "mainEntityOfPage": absolute_url(f"/guides/{article.get('slug','')}")
    }


def faq_schema(items):
    if not items:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": item.get("question"), "acceptedAnswer": {"@type": "Answer", "text": item.get("answer")}}
            for item in items if item.get("question") and item.get("answer")
        ],
    }


def json_ld(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
