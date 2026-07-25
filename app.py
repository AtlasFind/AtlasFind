from flask import Flask, render_template, request, abort, jsonify
import json
from pathlib import Path
from urllib.parse import urlencode

from tool_schema import validate_tools
from search_engine import alternative_queries, rank_tools, search_suggestions
from content_schema import validate_articles
from freshness import content_freshness, tool_freshness
from recommendation_engine import (
    RECOMMENDATION_PURPOSES,
    parse_recommendation_preferences,
    recommendation_requested,
    recommend_tools,
    score_recommendation,
)


app = Flask(__name__)

APP_VERSION = "0.4.1"

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "tools.json"
ARTICLE_FILE = BASE_DIR / "data" / "articles.json"

def load_tools():
    """
    JSON dosyasındaki bütün araçları okur.
    """
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            tools = json.load(file)

        validation_errors = validate_tools(tools)
        if validation_errors:
            error_text = "\n".join(f"- {error}" for error in validation_errors)
            raise ValueError(
                "tools.json does not satisfy the AtlasFind tool schema:\n"
                f"{error_text}"
            )

        return tools

    except FileNotFoundError:
        print("tools.json dosyası bulunamadı.")
        return []

    except json.JSONDecodeError:
        print("tools.json dosyasının biçimi bozuk.")
        return []

    except ValueError as error:
        print(error)
        return []



def load_articles():
    """Load and validate all editorial content."""
    try:
        with open(ARTICLE_FILE, "r", encoding="utf-8") as file:
            articles = json.load(file)

        tool_slugs = {tool.get("slug") for tool in load_tools()}
        validation_errors = validate_articles(articles, tool_slugs)
        if validation_errors:
            error_text = "\n".join(f"- {error}" for error in validation_errors)
            raise ValueError(
                "articles.json does not satisfy the AtlasFind content schema:\n"
                f"{error_text}"
            )
        return articles
    except FileNotFoundError:
        print("articles.json was not found.")
        return []
    except json.JSONDecodeError:
        print("articles.json contains invalid JSON.")
        return []
    except ValueError as error:
        print(error)
        return []


def find_article_by_slug(slug):
    return next((article for article in load_articles() if article.get("slug") == slug), None)


def article_tools(article, tools_by_slug):
    return [tools_by_slug[slug] for slug in article.get("related_tool_slugs", []) if slug in tools_by_slug]


def related_articles_for(article, all_articles, limit=3):
    by_slug = {item.get("slug"): item for item in all_articles}
    selected = []
    for slug in article.get("related_article_slugs", []):
        item = by_slug.get(slug)
        if item and item.get("slug") != article.get("slug"):
            selected.append(item)
    if len(selected) < limit:
        for item in all_articles:
            if item.get("slug") == article.get("slug") or item in selected:
                continue
            if item.get("category") == article.get("category") or item.get("content_type") == article.get("content_type"):
                selected.append(item)
            if len(selected) >= limit:
                break
    return selected[:limit]

def find_tool_by_slug(slug):
    """
    Slug değerine göre tek bir araç bulur.
    """

    tools = load_tools()

    for tool in tools:
        if tool.get("slug") == slug:
            return tool

    return None


def calculate_alternative_score(source_tool, candidate_tool):
    """
    İki aracın ne kadar benzer olduğunu hesaplar.

    Aynı kategori:
    +5 puan

    Ortak her etiket:
    +2 puan

    Aynı platform:
    +1 puan
    """

    score = 0

    source_category = source_tool.get("category", "").lower()
    candidate_category = candidate_tool.get("category", "").lower()

    if source_category == candidate_category:
        score += 5

    source_tags = {
        tag.lower()
        for tag in source_tool.get("tags", [])
    }

    candidate_tags = {
        tag.lower()
        for tag in candidate_tool.get("tags", [])
    }

    common_tags = source_tags.intersection(candidate_tags)

    score += len(common_tags) * 2

    source_platforms = {
        platform.lower()
        for platform in source_tool.get("platforms", [])
    }

    candidate_platforms = {
        platform.lower()
        for platform in candidate_tool.get("platforms", [])
    }

    common_platforms = source_platforms.intersection(
        candidate_platforms
    )

    score += len(common_platforms)

    return score


def find_alternatives(source_tool, limit=6):
    """
    Seçilen araca benzeyen diğer araçları bulur.
    """

    tools = load_tools()
    scored_tools = []

    for candidate_tool in tools:

        if candidate_tool.get("id") == source_tool.get("id"):
            continue

        score = calculate_alternative_score(
            source_tool,
            candidate_tool
        )

        if score > 0:
            scored_tools.append({
                "tool": candidate_tool,
                "score": score
            })

    scored_tools.sort(
        key=lambda item: (
            item["score"],
            item["tool"].get("rating", 0)
        ),
        reverse=True
    )

    alternatives = [
        item["tool"]
        for item in scored_tools[:limit]
    ]

    return alternatives

def normalize_text(text):
    """
    Türkçe ve İngilizce aramalarda metni
    karşılaştırmaya uygun hâle getirir.
    """
    return str(text).strip().lower()


def detect_search_needs(search_query):
    """
    Kullanıcının yazdığı cümleden temel ihtiyaçları çıkarır.
    """

    query = normalize_text(search_query)

    detected_needs = []

    need_keywords = {
        "free": [
            "free",
            "ücretsiz",
            "bedava"
        ],

        "open_source": [
            "open source",
            "açık kaynak",
            "opensource"
        ],

        "offline": [
            "offline",
            "çevrimdışı",
            "internetsiz",
            "internet olmadan"
        ],

        "privacy": [
            "privacy",
            "gizlilik",
            "özel",
            "verilerimi koruyan"
        ],

        "lightweight": [
            "lightweight",
            "hafif",
            "eski bilgisayar",
            "düşük sistem",
            "düşük donanım",
            "az ram"
        ],

        "ai": [
            "ai",
            "yapay zeka",
            "yapay zekâ"
        ],

        "photo_editing": [
            "photoshop",
            "fotoğraf",
            "photo editing",
            "resim düzenleme"
        ],

        "video_editing": [
            "video editor",
            "video düzenleme",
            "video editörü",
            "premiere"
        ],

        "code_editor": [
            "code editor",
            "kod editörü",
            "kodlama",
            "visual studio code",
            "vscode"
        ],

        "browser": [
            "browser",
            "tarayıcı",
            "chrome",
            "firefox"
        ],

        "local_ai": [
            "local ai",
            "yerel ai",
            "yerel yapay zeka",
            "bilgisayarımda çalışan ai"
        ]
    }

    for need_name, keywords in need_keywords.items():
        for keyword in keywords:
            if keyword in query:
                detected_needs.append(need_name)
                break

    return detected_needs


def calculate_search_score(tool, search_query, detected_needs):
    """
    Bir aracın kullanıcının aramasına ne kadar uyduğunu hesaplar.
    """

    score = 0

    query = normalize_text(search_query)

    name = normalize_text(tool.get("name", ""))
    description = normalize_text(tool.get("description", ""))
    category = normalize_text(tool.get("category", ""))

    tags = [
        normalize_text(tag)
        for tag in tool.get("tags", [])
    ]

    platforms = [
        normalize_text(platform)
        for platform in tool.get("platforms", [])
    ]

    pricing = normalize_text(tool.get("pricing", ""))

    searchable_text = " ".join([
        name,
        description,
        category,
        " ".join(tags),
        " ".join(platforms),
        pricing
    ])

    # Tam ürün adı eşleşmesi
    if query == name:
        score += 100

    # Ürün adı arama içinde geçiyorsa
    elif name in query or query in name:
        score += 60

    # Arama kelimeleri
    query_words = query.split()

    for word in query_words:
        if len(word) < 2:
            continue

        if word in name:
            score += 20

        if word in category:
            score += 12

        if word in tags:
            score += 10

        if word in description:
            score += 5

        if word in searchable_text:
            score += 2

    # Algılanan ihtiyaçlara göre puanlama
    if "free" in detected_needs:
        if pricing == "free":
            score += 35
        elif pricing == "freemium":
            score += 15

    if "open_source" in detected_needs:
        if tool.get("open_source", False):
            score += 35

    if "offline" in detected_needs:
        if tool.get("offline", False):
            score += 30

    if "privacy" in detected_needs:
        privacy_tags = {
            "privacy",
            "encryption",
            "local ai",
            "local first",
            "self hosted"
        }

        if any(tag in privacy_tags for tag in tags):
            score += 25

        if tool.get("offline", False):
            score += 10

        if tool.get("open_source", False):
            score += 8

    if "lightweight" in detected_needs:
        lightweight_tags = {
            "lightweight",
            "fast",
            "simple",
            "minimal"
        }

        if any(tag in lightweight_tags for tag in tags):
            score += 30

    if "ai" in detected_needs:
        if tool.get("ai_powered", False):
            score += 25

    if "photo_editing" in detected_needs:
        if category == "design":
            score += 25

        if any(
            tag in tags
            for tag in [
                "photo editing",
                "raster",
                "digital painting"
            ]
        ):
            score += 30

    if "video_editing" in detected_needs:
        if category == "video":
            score += 30

        if "video editing" in tags:
            score += 25

    if "code_editor" in detected_needs:
        if category == "development":
            score += 25

        if any(
            tag in tags
            for tag in [
                "code editor",
                "ide",
                "text editor"
            ]
        ):
            score += 30

    if "browser" in detected_needs:
        if category == "browser":
            score += 40

    if "local_ai" in detected_needs:
        if "local ai" in tags:
            score += 45

        if tool.get("offline", False):
            score += 20

        if category == "artificial intelligence":
            score += 20

    # Puanı çok düşük araçları sonuçlara alma
    return score


PLATFORM_ALIASES = {
    "windows": "windows",
    "macos": "macos",
    "mac": "macos",
    "linux": "linux",
    "android": "android",
    "ios": "ios",
    "ipados": "ios",
    "web": "web",
}


def normalize_platform(value):
    return PLATFORM_ALIASES.get(normalize_text(value).replace(" ", ""), "")


def parse_filters(args):
    pricing = [
        normalize_text(value)
        for value in args.getlist("pricing")
        if normalize_text(value) in {"free", "freemium", "paid"}
    ]
    platforms = [
        normalize_platform(value)
        for value in args.getlist("platform")
        if normalize_platform(value)
    ]
    system_levels = [
        normalize_text(value)
        for value in args.getlist("system_level")
        if normalize_text(value) in {"light", "medium", "heavy", "unknown"}
    ]

    max_ram_raw = args.get("max_ram", "").strip()
    try:
        max_ram = float(max_ram_raw) if max_ram_raw else None
        if max_ram is not None and max_ram <= 0:
            max_ram = None
    except ValueError:
        max_ram = None

    return {
        "pricing": pricing,
        "platforms": platforms,
        "system_levels": system_levels,
        "open_source": args.get("open_source") == "1",
        "offline": args.get("offline") == "1",
        "ai": args.get("ai") == "1",
        "turkish": args.get("turkish") == "1",
        "max_ram": max_ram,
    }


def tool_matches_filters(tool, filters):
    if filters["pricing"]:
        pricing_type = normalize_text(tool.get("pricing_type", tool.get("pricing", "")))
        if pricing_type not in filters["pricing"]:
            return False

    if filters["platforms"]:
        tool_platforms = {normalize_platform(value) for value in tool.get("platforms", [])}
        if not tool_platforms.intersection(filters["platforms"]):
            return False

    if filters["system_levels"]:
        if normalize_text(tool.get("system_level", "unknown")) not in filters["system_levels"]:
            return False

    if filters["open_source"] and not bool(tool.get("open_source", False)):
        return False
    if filters["offline"] and not bool(tool.get("offline", False)):
        return False
    if filters["ai"] and not bool(tool.get("ai_powered", False)):
        return False
    if filters["turkish"]:
        languages = {normalize_text(value) for value in tool.get("languages", [])}
        if "tr" not in languages:
            return False

    if filters["max_ram"] is not None:
        minimum_ram = tool.get("minimum_ram_gb")
        if not isinstance(minimum_ram, (int, float)) or isinstance(minimum_ram, bool):
            return False
        if minimum_ram > filters["max_ram"]:
            return False

    return True


def filter_tools(tools, filters):
    return [tool for tool in tools if tool_matches_filters(tool, filters)]


def build_query_url(search_query, filters, remove=None):
    params = []
    if search_query:
        params.append(("q", search_query))

    for value in filters["pricing"]:
        if remove != ("pricing", value):
            params.append(("pricing", value))
    for value in filters["platforms"]:
        if remove != ("platform", value):
            params.append(("platform", value))
    for value in filters["system_levels"]:
        if remove != ("system_level", value):
            params.append(("system_level", value))

    for key in ("open_source", "offline", "ai", "turkish"):
        if filters[key] and remove != (key, "1"):
            params.append((key, "1"))

    if filters["max_ram"] is not None and remove != ("max_ram", str(filters["max_ram"])):
        value = int(filters["max_ram"]) if filters["max_ram"].is_integer() else filters["max_ram"]
        params.append(("max_ram", str(value)))

    query = urlencode(params, doseq=True)
    return f"/?{query}" if query else "/"


def build_active_filters(search_query, filters):
    labels = {
        "free": "Free", "freemium": "Freemium", "paid": "Paid",
        "windows": "Windows", "macos": "macOS", "linux": "Linux",
        "android": "Android", "ios": "iOS", "web": "Web",
        "light": "Light system", "medium": "Medium system",
        "heavy": "Heavy system", "unknown": "Unknown system",
    }
    active = []
    for value in filters["pricing"]:
        active.append({"label": labels[value], "url": build_query_url(search_query, filters, ("pricing", value))})
    for value in filters["platforms"]:
        active.append({"label": labels[value], "url": build_query_url(search_query, filters, ("platform", value))})
    for value in filters["system_levels"]:
        active.append({"label": labels[value], "url": build_query_url(search_query, filters, ("system_level", value))})
    for key, label in (("open_source", "Open source"), ("offline", "Offline"), ("ai", "AI-powered"), ("turkish", "Turkish support")):
        if filters[key]:
            active.append({"label": label, "url": build_query_url(search_query, filters, (key, "1"))})
    if filters["max_ram"] is not None:
        value = int(filters["max_ram"]) if filters["max_ram"].is_integer() else filters["max_ram"]
        active.append({"label": f"Up to {value} GB RAM", "url": build_query_url(search_query, filters, ("max_ram", str(filters["max_ram"])))})
    return active


def calculate_match_percentage(score, highest_score):
    """
    Sonuçları 0-100 arasında yüzdelik değere dönüştürür.
    """

    if highest_score <= 0:
        return 0

    percentage = round(
        (score / highest_score) * 100
    )

    return min(percentage, 100)



CATEGORY_INFO = {
    "artificial-intelligence": {"name": "Artificial Intelligence", "description": "AI assistants, local models and intelligent creative tools."},
    "development": {"name": "Development", "description": "Editors, IDEs and utilities for building software."},
    "design": {"name": "Design", "description": "Visual design, illustration and interface creation tools."},
    "video": {"name": "Video", "description": "Editing, recording, animation and production software."},
    "audio": {"name": "Audio", "description": "Audio editing, music production and podcast tools."},
    "office": {"name": "Office", "description": "Documents, notes, planning and productivity tools."},
    "browser": {"name": "Browser", "description": "Web browsers focused on speed, privacy and workflows."},
    "cloud": {"name": "Cloud", "description": "Cloud storage, hosting and deployment platforms."},
    "security": {"name": "Security", "description": "Privacy, account and device protection tools."},
    "database": {"name": "Database", "description": "Database engines, clients and data management tools."},
}
COLLECTION_INFO = {
    "free-tools": {"name": "Free Tools", "description": "Tools with a fully free pricing model."},
    "open-source": {"name": "Open Source", "description": "Software whose source code can be inspected and improved."},
    "low-end-pc": {"name": "Low-end PC", "description": "Lightweight tools suitable for modest hardware."},
    "students": {"name": "For Students", "description": "Accessible tools suited to learning and student workflows."},
    "editor-choice": {"name": "Editor Choices", "description": "Strong all-round tools selected by AtlasFind editorial rules."},
}

def slugify_category(name):
    return normalize_text(name).replace(" ", "-")

def sort_tools(items, sort_key):
    options = {
        "rating": lambda t: (-float(t.get("rating", 0)), normalize_text(t.get("name", ""))),
        "popular": lambda t: (-int(t.get("popularity_score", 0)), normalize_text(t.get("name", ""))),
        "newest": lambda t: (str(t.get("date_added", "")), normalize_text(t.get("name", ""))),
        "name-asc": lambda t: normalize_text(t.get("name", "")),
        "name-desc": lambda t: normalize_text(t.get("name", "")),
        "ram": lambda t: (t.get("minimum_ram_gb") is None, t.get("minimum_ram_gb") or 9999, normalize_text(t.get("name", ""))),
    }
    key = sort_key if sort_key in options else "popular"
    reverse = key in {"newest", "name-desc"}
    return sorted(items, key=options[key], reverse=reverse)

def paginate(items, page, per_page=18):
    total=len(items); pages=max(1,(total+per_page-1)//per_page); page=max(1,min(page,pages))
    start=(page-1)*per_page
    return items[start:start+per_page], {"page":page,"pages":pages,"total":total,"has_prev":page>1,"has_next":page<pages}

def discovery_context(items, title, description, page_type):
    filters=parse_filters(request.args)
    items=filter_tools(items,filters)
    subcategory=request.args.get("subcategory","").strip()
    if subcategory:
        items=[t for t in items if t.get("subcategory")==subcategory]
    sort_key=request.args.get("sort","popular")
    items=sort_tools(items,sort_key)
    try: page=int(request.args.get("page","1"))
    except ValueError: page=1
    page_items,pagination=paginate(items,page)
    subcategories=sorted({t.get("subcategory") for t in items if t.get("subcategory")})
    return dict(tools=page_items,title=title,description=description,page_type=page_type,filters=filters,sort_key=sort_key,subcategory=subcategory,subcategories=subcategories,pagination=pagination,query_args=request.args)


@app.context_processor
def inject_app_metadata():
    return {"app_version": APP_VERSION}

@app.route("/")
def home():
    all_tools = load_tools()
    search_query = request.args.get("q", "").strip()
    filters = parse_filters(request.args)
    search_meta = {"detected_needs": [], "corrected_query": search_query, "did_correct": False}

    if search_query:
        ranked_tools, search_meta = rank_tools(all_tools, search_query)
    else:
        ranked_tools = [
            {"tool": tool, "score": 0, "match": None, "reasons": []}
            for tool in sorted(all_tools, key=lambda tool: tool.get("rating", 0), reverse=True)
        ]

    # Keep every result entry template-safe, including unsearched home-page cards.
    for item in ranked_tools:
        item.setdefault("reasons", [])
        item.setdefault("match", None)

    ranked_tools = [item for item in ranked_tools if tool_matches_filters(item["tool"], filters)]
    tools = [item["tool"] for item in ranked_tools]
    active_filters = build_active_filters(search_query, filters)
    alternatives = alternative_queries(
        search_query,
        search_meta.get("corrected_query", search_query),
        search_meta.get("detected_needs", []),
    ) if search_query and not tools else []

    return render_template(
        "index.html",
        tools=tools,
        ranked_tools=ranked_tools,
        search_query=search_query,
        corrected_query=search_meta.get("corrected_query", search_query),
        did_correct=search_meta.get("did_correct", False),
        search_alternatives=alternatives,
        detected_needs=search_meta.get("detected_needs", []),
        filters=filters,
        active_filters=active_filters,
        clear_filters_url=f"/?{urlencode({'q': search_query})}" if search_query else "/",
        total_tool_count=len(all_tools),
        result_count=len(tools),
        categories=[dict(slug=slug, **info, count=sum(1 for t in all_tools if slugify_category(t.get("category", "")) == slug)) for slug, info in CATEGORY_INFO.items()],
        popular_tools=sort_tools(all_tools, "popular")[:6],
        newest_tools=sort_tools(all_tools, "newest")[:6],
        editor_tools=[t for t in sort_tools(all_tools, "rating") if t.get("editor_choice")][:6],
        collections=COLLECTION_INFO,
    )


@app.route("/api/search-suggestions")
def search_suggestions_api():
    query = request.args.get("q", "").strip()
    return jsonify(search_suggestions(load_tools(), query))


@app.route("/categories/<slug>")
def category_page(slug):
    info=CATEGORY_INFO.get(slug)
    if not info: abort(404)
    items=[t for t in load_tools() if slugify_category(t.get("category",""))==slug]
    related_guides = [article for article in load_articles() if article.get("category") == slug]
    return render_template("discovery.html", **discovery_context(items, info["name"], info["description"], "category"), active_page="categories", related_guides=related_guides)

@app.route("/collections/<slug>")
def collection_page(slug):
    info=COLLECTION_INFO.get(slug)
    if not info: abort(404)
    items=[t for t in load_tools() if slug in t.get("collections",[])]
    return render_template("discovery.html", **discovery_context(items, info["name"], info["description"], "collection"), active_page="categories", related_guides=[])



@app.route("/guides")
def guides():
    articles = load_articles()
    content_type = request.args.get("type", "").strip()
    category = request.args.get("category", "").strip()
    filtered = articles
    if content_type:
        filtered = [article for article in filtered if article.get("content_type") == content_type]
    if category:
        filtered = [article for article in filtered if article.get("category") == category]
    filtered = sorted(filtered, key=lambda article: (article.get("updated_at", ""), article.get("title", "")), reverse=True)
    return render_template(
        "guides.html",
        active_page="guides",
        articles=filtered,
        all_articles=articles,
        selected_type=content_type,
        selected_category=category,
        content_types=sorted({article.get("content_type") for article in articles}),
        article_categories=sorted({article.get("category") for article in articles}),
    )


@app.route("/guides/<slug>")
def article_detail(slug):
    article = find_article_by_slug(slug)
    if article is None:
        abort(404)
    all_articles = load_articles()
    tools = load_tools()
    tools_by_slug = {tool.get("slug"): tool for tool in tools}
    section_tools = {
        section.get("id"): [tools_by_slug[item] for item in section.get("tool_slugs", []) if item in tools_by_slug]
        for section in article.get("sections", [])
    }
    return render_template(
        "article.html",
        active_page="guides",
        article=article,
        related_tools=article_tools(article, tools_by_slug),
        related_articles=related_articles_for(article, all_articles),
        section_tools=section_tools,
        category_info=CATEGORY_INFO.get(article.get("category")),
        freshness=content_freshness(article.get("updated_at")),
    )

@app.route("/recommend")
def recommend():
    preferences = parse_recommendation_preferences(request.args)
    submitted = recommendation_requested(preferences)
    recommendations = recommend_tools(load_tools(), preferences) if submitted else []
    return render_template(
        "recommend.html",
        active_page="recommend",
        preferences=preferences,
        purpose_options=RECOMMENDATION_PURPOSES,
        recommendations=recommendations,
        submitted=submitted,
    )

@app.route("/tools/<slug>")
def tool_detail(slug):
    tool = find_tool_by_slug(slug)

    if tool is None:
        abort(404)

    alternatives = find_alternatives(
        tool,
        limit=6
    )

    return render_template(
        "tool.html",
        tool=tool,
        alternatives=alternatives,
        freshness=tool_freshness(tool),
    )


def _comparison_value(tool, key):
    if key == "category":
        return tool.get("category") or "Unknown"
    if key == "pricing":
        return tool.get("pricing") or tool.get("pricing_type") or "Unknown"
    if key in {"open_source", "offline", "ai_powered"}:
        return "Yes" if tool.get(key, False) else "No"
    if key == "platforms":
        values = tool.get("platforms") or []
        return ", ".join(platform_label(normalize_platform(value)) for value in values) or "Unknown"
    if key == "minimum_ram_gb":
        value = tool.get("minimum_ram_gb")
        return f"{value:g} GB" if isinstance(value, (int, float)) and not isinstance(value, bool) else "Unknown"
    if key == "system_level":
        value = normalize_text(tool.get("system_level", "unknown"))
        return value.title() if value else "Unknown"
    if key == "languages":
        values = tool.get("languages") or []
        return ", ".join(value.upper() for value in values) or "Unknown"
    if key == "rating":
        value = tool.get("rating")
        return f"{value} / 5" if value is not None else "Unknown"
    if key == "target_users":
        return ", ".join(tool.get("target_users") or []) or "Unknown"
    return str(tool.get(key) or "Unknown")


def build_comparison_rows(tools):
    definitions = [
        ("Category", "category"),
        ("Pricing", "pricing"),
        ("Open source", "open_source"),
        ("Offline support", "offline"),
        ("AI features", "ai_powered"),
        ("Platforms", "platforms"),
        ("Minimum RAM", "minimum_ram_gb"),
        ("System level", "system_level"),
        ("Languages", "languages"),
        ("Rating", "rating"),
        ("Target users", "target_users"),
    ]
    rows = []
    for label, key in definitions:
        values = [_comparison_value(tool, key) for tool in tools]
        rows.append({"label": label, "key": key, "values": values, "common": len(set(values)) <= 1})
    return rows


@app.route("/compare")
def compare_tools():
    requested_slugs = [slug.strip() for slug in request.args.getlist("tools") if slug.strip()]

    # Keep old v0.2.1 links working.
    if not requested_slugs:
        requested_slugs = [
            request.args.get("left", "").strip(),
            request.args.get("right", "").strip(),
        ]
        requested_slugs = [slug for slug in requested_slugs if slug]

    unique_slugs = []
    for slug in requested_slugs:
        if slug not in unique_slugs:
            unique_slugs.append(slug)
    unique_slugs = unique_slugs[:4]

    selected_tools = []
    for slug in unique_slugs:
        tool = find_tool_by_slug(slug)
        if tool is None:
            abort(404)
        selected_tools.append(tool)

    hide_common = request.args.get("hide_common") == "1"
    rows = build_comparison_rows(selected_tools) if len(selected_tools) >= 2 else []
    visible_rows = [row for row in rows if not (hide_common and row["common"])]

    preferences = parse_recommendation_preferences(request.args)
    preference_submitted = recommendation_requested(preferences)
    scored_tools = [score_recommendation(tool, preferences) for tool in selected_tools] if preference_submitted else []
    scored_tools.sort(key=lambda item: (item["match"], item["score"], item["tool"].get("rating", 0)), reverse=True)
    winner = scored_tools[0] if scored_tools else None

    return render_template(
        "compare.html",
        selected_tools=selected_tools,
        selected_slugs=unique_slugs,
        comparison_rows=visible_rows,
        all_rows=rows,
        hide_common=hide_common,
        all_tools=sorted(load_tools(), key=lambda tool: tool.get("name", "")),
        preferences=preferences,
        purpose_options=RECOMMENDATION_PURPOSES,
        preference_submitted=preference_submitted,
        scored_tools=scored_tools,
        winner=winner,
    )


if __name__ == "__main__":
    app.run(debug=True)