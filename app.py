from flask import Flask, render_template, request, abort, jsonify, Response, redirect, g, url_for, has_request_context, session
from pathlib import Path
from functools import lru_cache
import os
import secrets
import uuid
from urllib.parse import urlencode

from tool_schema import validate_tools
from search_engine import alternative_queries, rank_tools, search_suggestions
from content_schema import validate_articles
from freshness import content_freshness, tool_freshness
from repositories.tools import get_all_tools, get_tool_by_slug
from repositories.articles import get_all_articles, get_article_by_slug
from repositories.translations import localize_tool, localize_article, localize_tools, localize_articles
from services.image_service import enrich_tool_branding
from services.rating_service import enrich_tool_rating
from repositories.user_reviews import aggregate_user_rating, anonymous_user_key, upsert_review
from repositories.admin import record_visit
from database import DATABASE_PATH, apply_migrations
from i18n import DEFAULT_LOCALE, SUPPORTED_LOCALES, get_locale, translate, localized_path, alternate_urls
from admin import admin_bp
from admin.bootstrap import bootstrap_admin_from_environment, reset_admin_password_from_environment
from security import (
    add_security_headers, client_ip, configure_logging, configure_security, enforce_api_rate_limit,
    enforce_safe_method, new_request_id, validate_request_host,
)
from taxonomy import CATEGORIES, category_slug, localized_category
from seo import (
    SITE_URL, absolute_url, article_schema, breadcrumb_schema, breadcrumbs as build_breadcrumbs,
    faq_schema, json_ld, page_seo, software_schema, website_schema,
)

from recommendation_engine import (
    RECOMMENDATION_PURPOSES,
    parse_recommendation_preferences,
    recommendation_requested,
    recommend_tools,
    score_recommendation,
)


app = Flask(__name__)
configure_security(app)
configure_logging(app)
apply_migrations()
bootstrap_status = bootstrap_admin_from_environment(app.config["PRODUCTION"])
if bootstrap_status != "disabled":
    # Never log credentials; this is solely a deployment diagnostic for hosts
    # that do not provide an interactive shell on their free tier.
    app.logger.warning("production_admin_bootstrap_status=%s", bootstrap_status)
password_reset_status = reset_admin_password_from_environment(app.config["PRODUCTION"])
if password_reset_status != "disabled":
    app.logger.warning("production_admin_password_reset_status=%s", password_reset_status)
app.register_blueprint(admin_bp)

APP_VERSION = "1.0.8"

CONTACT_EMAIL = os.getenv("ATLASFIND_CONTACT_EMAIL", "atlasfindd@gmail.com").strip() or "atlasfindd@gmail.com"


PUBLIC_PAGES = {
    "collaborate": {
        "en": {"title": "Collaborate with AtlasFind", "description": "Partnership, creator and editorial collaboration opportunities with AtlasFind.", "sections": [
            ("A focused software discovery platform", "AtlasFind is a bilingual software discovery and comparison platform covering 600 tools across 18 main categories and 159 subcategories. It helps visitors narrow broad software choices into relevant categories and meaningful comparisons."),
            ("Who we can work with", "We are open to hearing from creators, educators, software communities, independent developers, technology publications and brands whose work is relevant to software discovery, productivity and digital tools."),
            ("Possible collaboration formats", "Relevant formats may include an AtlasFind introduction, educational software guides, category-focused content, tool discovery campaigns, community feedback projects and clearly disclosed sponsored collaborations."),
            ("Editorial independence", "Payment or partnership does not guarantee a positive ranking, rating or recommendation. Sponsored activity must be clearly disclosed, and factual product claims should be supported by official sources."),
            ("Current project stage", "AtlasFind is a continuously developing public-beta project. Its catalog, interface, comparison rules and data quality processes are actively improved as the platform prepares for wider audiences."),
            ("Start a conversation", "Send a short introduction, your channel or project link, audience focus and collaboration idea to atlasfindd@gmail.com. We can then discuss whether the idea is relevant for both audiences."),
        ]},
        "tr": {"title": "AtlasFind ile İş Birliği", "description": "AtlasFind ile içerik üreticisi, yayın ve marka iş birliği fırsatları.", "sections": [
            ("Odaklı bir yazılım keşif platformu", "AtlasFind; 18 ana kategori ve 159 alt kategoride 600 aracı kapsayan, Türkçe ve İngilizce çalışan bir yazılım keşif ve karşılaştırma platformudur. Ziyaretçilerin geniş yazılım seçeneklerini ilgili kategorilere ve anlamlı karşılaştırmalara indirmesine yardımcı olur."),
            ("Kimlerle çalışabiliriz?", "İçerik üreticileri, eğitimciler, yazılım toplulukları, bağımsız geliştiriciler, teknoloji yayınları ve yazılım keşfi, üretkenlik veya dijital araçlarla ilgili markalardan gelecek fikirleri değerlendirmeye açığız."),
            ("İş birliği biçimleri", "AtlasFind tanıtımı, eğitici yazılım rehberleri, kategori odaklı içerikler, araç keşif kampanyaları, topluluk geri bildirim projeleri ve açıkça belirtilen sponsorlu çalışmalar değerlendirilebilir."),
            ("Editoryal bağımsızlık", "Ödeme veya iş birliği; olumlu sıralama, puan ya da öneri garantisi vermez. Sponsorlu çalışmalar açıkça belirtilir ve ürünle ilgili önemli iddialar resmî kaynaklarla desteklenmelidir."),
            ("Projenin mevcut aşaması", "AtlasFind sürekli geliştirilen bir public beta projesidir. Daha geniş kitlelere hazırlanırken katalog, arayüz, karşılaştırma kuralları ve veri kalitesi süreçleri aktif biçimde iyileştirilmektedir."),
            ("İlk adımı atalım", "Kısa bir tanıtım, kanal veya proje bağlantınız, hedef kitleniz ve iş birliği fikrinizle birlikte atlasfindd@gmail.com adresine yazabilirsiniz. Ardından fikrin iki tarafın kitlesi için de uygun olup olmadığını konuşabiliriz."),
        ]},
    },
    "about": {
        "en": {"title": "About AtlasFind", "description": "Why AtlasFind exists, how the project works and where it is heading.", "sections": [
            ("Why we built AtlasFind", "AtlasFind was created to make software discovery less confusing. It brings tools from different fields into one independent catalog so visitors can explore, filter and compare options before choosing what fits their workflow."),
            ("What the site provides", "The catalog organizes software by category and subcategory, presents practical product information, and offers contextual comparisons. AtlasFind does not sell the listed products and is not an official representative of their providers."),
            ("A continuously developing demo", "AtlasFind is still a demo and public-beta project. Pages, descriptions, categories, logos, comparison rules and technical infrastructure are reviewed and improved continuously. Some information may be incomplete or change while the project develops."),
            ("Independent and transparent", "The aim is to help people make a more informed first comparison without presenting paid placement as an objective recommendation. Important prices, features and availability should always be confirmed on the product's official website."),
            ("Contact and feedback", "Incorrect information, missing tools, improvement ideas and collaboration requests can be sent to atlasfindd@gmail.com. Clear reports with a page link and official source help us improve the catalog faster."),
        ]},
        "tr": {"title": "AtlasFind Hakkında", "description": "AtlasFind'in neden kurulduğu, nasıl çalıştığı ve nereye doğru geliştiği.", "sections": [
            ("AtlasFind'i neden kurduk?", "AtlasFind, yazılım keşfetmeyi daha anlaşılır hâle getirmek için kuruldu. Farklı alanlardaki araçları bağımsız bir katalogda bir araya getirerek ziyaretçilerin kendi çalışma biçimine uygun seçenekleri keşfetmesini, filtrelemesini ve karşılaştırmasını amaçlıyoruz."),
            ("Sitede neler sunuyoruz?", "Yazılımları ana kategori ve alt kategorilere ayırıyor, pratik ürün bilgileri sunuyor ve aynı kullanım alanındaki araçların anlamlı biçimde karşılaştırılmasını sağlıyoruz. AtlasFind listelenen ürünleri satmaz ve bu firmaların resmî temsilcisi değildir."),
            ("Sürekli gelişen bir demo", "AtlasFind hâlâ demo ve public beta aşamasındadır. Sayfalar, açıklamalar, kategoriler, logolar, karşılaştırma kuralları ve teknik altyapı sürekli kontrol edilip geliştirilmektedir. Proje gelişirken bazı bilgiler eksik kalabilir veya değişebilir."),
            ("Bağımsız ve şeffaf yaklaşım", "Amacımız ücretli yerleşimleri tarafsız öneri gibi göstermeden, kullanıcıların daha bilinçli bir ilk karşılaştırma yapmasına yardımcı olmaktır. Önemli fiyat, özellik ve erişilebilirlik bilgileri her zaman ürünün resmî sitesinden doğrulanmalıdır."),
            ("İletişim ve geri bildirim", "Yanlış bilgiler, eksik araçlar, geliştirme fikirleri ve iş birliği talepleri için atlasfindd@gmail.com adresinden bize ulaşabilirsiniz. Sayfa bağlantısı ve resmî kaynak içeren açık bildirimler kataloğu daha hızlı geliştirmemize yardımcı olur."),
        ]},
    },
    "privacy": {
        "en": {"title": "Privacy Policy", "description": "How AtlasFind handles technical data and protects visitor privacy.", "sections": [
            ("What we collect", "AtlasFind does not require a visitor account. The service may process standard server logs such as IP address, browser information, requested pages and timestamps for security, reliability and abuse prevention."),
            ("Cookies and local storage", "AtlasFind uses essential browser storage for interface preferences such as language, theme and cookie notice status. Advertising or analytics cookies are not enabled unless the policy is updated and consent is collected where required."),
            ("External websites", "Tool pages link to third-party websites. Their privacy practices and content are controlled by those providers, not AtlasFind."),
            ("Data retention", "Security and error logs are retained only as long as reasonably needed to operate and protect the service."),
            ("Contact", "Questions about privacy can be sent to the contact address shown on this page."),
        ]},
        "tr": {"title": "Gizlilik Politikası", "description": "AtlasFind'in teknik verileri nasıl işlediği ve ziyaretçi gizliliğini nasıl koruduğu.", "sections": [
            ("Topladığımız bilgiler", "AtlasFind ziyaretçi hesabı gerektirmez. Güvenlik, hizmet sürekliliği ve kötüye kullanımın önlenmesi amacıyla IP adresi, tarayıcı bilgisi, istenen sayfalar ve zaman bilgisi gibi standart sunucu kayıtları işlenebilir."),
            ("Çerezler ve yerel depolama", "AtlasFind dil, tema ve çerez bildirimi tercihi gibi temel arayüz ayarları için gerekli tarayıcı depolamasını kullanır. Politika güncellenmeden ve gerektiğinde izin alınmadan reklam veya analiz çerezleri etkinleştirilmez."),
            ("Haricî siteler", "Araç sayfaları üçüncü taraf sitelere bağlantı verir. Bu sitelerin içerik ve gizlilik uygulamalarından AtlasFind sorumlu değildir."),
            ("Saklama süresi", "Güvenlik ve hata kayıtları yalnızca hizmeti işletmek ve korumak için makul ölçüde gerekli süre boyunca tutulur."),
            ("İletişim", "Gizlilik soruları atlasfindd@gmail.com adresine gönderilebilir."),
        ]}
    },
    "terms": {
        "en": {"title": "Terms of Use", "description": "Rules for using AtlasFind and its independent tool information.", "sections": [
            ("Informational service", "AtlasFind provides discovery, comparison and editorial information. It does not sell, license or guarantee third-party tools."),
            ("Accuracy", "Prices, features and availability can change. Visitors should confirm important details on the official provider website before purchasing or relying on a tool."),
            ("Acceptable use", "Do not attempt to disrupt the service, bypass security controls, scrape it abusively or submit unlawful content."),
            ("Intellectual property", "Third-party names and trademarks belong to their respective owners. AtlasFind branding, original writing and site code remain subject to their applicable rights and licences."),
            ("Limitation", "AtlasFind is provided as available without a guarantee that every listing is complete, current or suitable for a particular purpose."),
        ]},
        "tr": {"title": "Kullanım Koşulları", "description": "AtlasFind'in ve bağımsız araç bilgilerinin kullanım kuralları.", "sections": [
            ("Bilgilendirme hizmeti", "AtlasFind keşif, karşılaştırma ve editoryal bilgi sunar. Üçüncü taraf araçları satmaz, lisanslamaz veya garanti etmez."),
            ("Doğruluk", "Fiyatlar, özellikler ve erişilebilirlik değişebilir. Satın alma veya önemli bir karar öncesinde bilgiler resmî sağlayıcı sitesinden doğrulanmalıdır."),
            ("Kabul edilebilir kullanım", "Hizmeti aksatmaya, güvenlik kontrollerini aşmaya, aşırı veri toplamaya veya yasa dışı içerik göndermeye çalışmayın."),
            ("Fikrî mülkiyet", "Üçüncü taraf adları ve markaları ilgili sahiplerine aittir. AtlasFind markası, özgün içerikleri ve site kodu geçerli hak ve lisanslara tabidir."),
            ("Sorumluluk sınırı", "AtlasFind mevcut hâliyle sunulur; her kaydın eksiksiz, güncel veya belirli bir amaca uygun olduğu garanti edilmez."),
        ]}
    },
    "cookies": {
        "en": {"title": "Cookie Policy", "description": "Essential storage used by AtlasFind.", "sections": [
            ("Essential preferences", "AtlasFind stores language, theme and cookie-notice choices in local storage so the interface works consistently."),
            ("No advertising cookies yet", "The public beta does not intentionally set advertising or cross-site tracking cookies. This page will be updated before such technology is introduced."),
            ("Managing storage", "You can clear AtlasFind site data from your browser settings. Doing so resets saved interface preferences."),
        ]},
        "tr": {"title": "Çerez Politikası", "description": "AtlasFind tarafından kullanılan gerekli tarayıcı depolaması.", "sections": [
            ("Gerekli tercihler", "AtlasFind arayüzün tutarlı çalışması için dil, tema ve çerez bildirimi tercihlerini yerel depolamada saklar."),
            ("Henüz reklam çerezi yok", "Public beta sürümü bilerek reklam veya siteler arası takip çerezi yerleştirmez. Böyle bir teknoloji eklenmeden önce bu sayfa güncellenecektir."),
            ("Depolamayı yönetme", "Tarayıcı ayarlarından AtlasFind site verilerini silebilirsiniz. Bu işlem kayıtlı arayüz tercihlerini sıfırlar."),
        ]}
    },
    "contact": {
        "en": {"title": "Contact AtlasFind", "description": "Report an issue, suggest a tool or contact the AtlasFind project.", "sections": [
            ("Suggest a tool", "Use the recommendation and suggestion page to share a tool that should be reviewed for the directory."),
            ("Report incorrect information", "Open an issue on the AtlasFind GitHub repository and include the tool name, official source and the information that should be corrected."),
            ("Public beta support", "AtlasFind is an early public beta. Reports that include a page address, screenshot and clear reproduction steps are the most useful."),
        ]},
        "tr": {"title": "AtlasFind ile İletişim", "description": "Sorun bildirin, araç önerin veya AtlasFind projesiyle iletişime geçin.", "sections": [
            ("Araç öner", "Dizinde incelenmesini istediğiniz aracı paylaşmak için öneri sayfasını kullanın."),
            ("Yanlış bilgi bildir", "AtlasFind GitHub deposunda bir konu açın; araç adını, resmî kaynağı ve düzeltilmesi gereken bilgiyi ekleyin."),
            ("Public beta desteği", "AtlasFind erken public beta aşamasındadır. Sayfa adresi, ekran görüntüsü ve açık tekrar adımları içeren bildirimler en yararlı olanlardır."),
        ]}
    },
}

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "tools.json"
ARTICLE_FILE = BASE_DIR / "data" / "articles.json"

def _database_version():
    try:
        return DATABASE_PATH.stat().st_mtime_ns
    except FileNotFoundError:
        return 0


def _normalize_tool_icons(tools):
    """Apply the central local-first v1.0.4 branding resolver."""
    return [enrich_tool_branding(tool) for tool in tools]


@lru_cache(maxsize=8)
def _cached_tools(locale, database_version):
    tools = [enrich_tool_rating(tool) for tool in _normalize_tool_icons(localize_tools(get_all_tools(), locale))]
    validation_errors = validate_tools(tools)
    if validation_errors:
        error_text = "\n".join(f"- {error}" for error in validation_errors)
        print("SQLite tool data does not satisfy the AtlasFind tool schema:\n" + error_text)
        return tuple()
    return tuple(tools)


@lru_cache(maxsize=8)
def _cached_articles(locale, database_version):
    articles = localize_articles(get_all_articles(), locale)
    tool_slugs = {tool.get("slug") for tool in _cached_tools(locale, database_version)}
    validation_errors = validate_articles(articles, tool_slugs)
    if validation_errors:
        error_text = "\n".join(f"- {error}" for error in validation_errors)
        print("SQLite article data does not satisfy the AtlasFind content schema:\n" + error_text)
        return tuple()
    return tuple(articles)


def load_tools(locale=None):
    """Return validated localized tools from an mtime-aware in-process cache."""
    locale = locale or (get_locale() if has_request_context() else DEFAULT_LOCALE)
    return list(_cached_tools(locale, _database_version()))


def load_articles(locale=None):
    """Return validated localized articles from an mtime-aware in-process cache."""
    locale = locale or (get_locale() if has_request_context() else DEFAULT_LOCALE)
    return list(_cached_articles(locale, _database_version()))


def find_article_by_slug(slug, locale=None):
    return localize_article(get_article_by_slug(slug), locale or get_locale())


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

def find_tool_by_slug(slug, locale=None):
    """Return a localized tool from the SQLite repository by slug."""
    tool = localize_tool(get_tool_by_slug(slug), locale or get_locale())
    return enrich_tool_branding(tool) if tool else None


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

    min_rating_raw = args.get("min_rating", "").strip()
    try:
        min_rating = float(min_rating_raw) if min_rating_raw else None
        if min_rating is not None and not 0 < min_rating <= 5:
            min_rating = None
    except ValueError:
        min_rating = None

    return {
        "category": args.get("category", "").strip(),
        "pricing": pricing,
        "platforms": platforms,
        "system_levels": system_levels,
        "open_source": args.get("open_source") == "1",
        "offline": args.get("offline") == "1",
        "ai": args.get("ai") == "1",
        "turkish": args.get("turkish") == "1",
        "max_ram": max_ram,
        "min_rating": min_rating,
    }


def tool_matches_filters(tool, filters):
    if filters.get("category") and tool.get("category") != filters["category"]:
        return False

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

    if filters.get("min_rating") is not None:
        try:
            if float(tool.get("rating", 0)) < filters["min_rating"]:
                return False
        except (TypeError, ValueError):
            return False

    return True


def filter_tools(tools, filters):
    return [tool for tool in tools if tool_matches_filters(tool, filters)]


def build_query_url(search_query, filters, remove=None, base_path="/", extra=None):
    params = []
    if search_query:
        params.append(("q", search_query))

    if filters.get("category") and remove != ("category", filters["category"]):
        params.append(("category", filters["category"]))
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
    if filters.get("min_rating") is not None and remove != ("min_rating", str(filters["min_rating"])):
        value = int(filters["min_rating"]) if filters["min_rating"].is_integer() else filters["min_rating"]
        params.append(("min_rating", str(value)))

    for key, value in (extra or {}).items():
        if value not in (None, "", False):
            params.append((key, value))

    query = urlencode(params, doseq=True)
    return f"{base_path}?{query}" if query else base_path


def build_active_filters(search_query, filters, base_path="/", locale="en", extra=None):
    labels = {
        "en": {
            "free": "Free", "freemium": "Freemium", "paid": "Paid",
            "windows": "Windows", "macos": "macOS", "linux": "Linux",
            "android": "Android", "ios": "iOS", "web": "Web",
            "light": "Light system", "medium": "Medium system",
            "heavy": "Heavy system", "unknown": "Unknown system",
            "open_source": "Open source", "offline": "Offline",
            "ai": "AI-powered", "turkish": "Turkish support",
            "ram": "Up to {value} GB RAM", "rating": "{value}+ rating",
        },
        "tr": {
            "free": "Ücretsiz", "freemium": "Ücretsiz + ücretli", "paid": "Ücretli",
            "windows": "Windows", "macos": "macOS", "linux": "Linux",
            "android": "Android", "ios": "iOS", "web": "Web",
            "light": "Hafif sistem", "medium": "Orta sistem",
            "heavy": "Güçlü sistem", "unknown": "Sistem bilgisi yok",
            "open_source": "Açık kaynak", "offline": "Çevrimdışı",
            "ai": "Yapay zekâ destekli", "turkish": "Türkçe desteği",
            "ram": "En fazla {value} GB RAM", "rating": "{value}+ puan",
        },
    }[locale if locale in {"tr", "en"} else "en"]
    active = []
    if filters.get("category"):
        active.append({"label": filters["category"], "url": build_query_url(search_query, filters, ("category", filters["category"]), base_path, extra)})
    for value in filters["pricing"]:
        active.append({"label": labels[value], "url": build_query_url(search_query, filters, ("pricing", value), base_path, extra)})
    for value in filters["platforms"]:
        active.append({"label": labels[value], "url": build_query_url(search_query, filters, ("platform", value), base_path, extra)})
    for value in filters["system_levels"]:
        active.append({"label": labels[value], "url": build_query_url(search_query, filters, ("system_level", value), base_path, extra)})
    for key in ("open_source", "offline", "ai", "turkish"):
        if filters[key]:
            active.append({"label": labels[key], "url": build_query_url(search_query, filters, (key, "1"), base_path, extra)})
    if filters["max_ram"] is not None:
        value = int(filters["max_ram"]) if filters["max_ram"].is_integer() else filters["max_ram"]
        active.append({"label": labels["ram"].format(value=value), "url": build_query_url(search_query, filters, ("max_ram", str(filters["max_ram"])), base_path, extra)})
    if filters.get("min_rating") is not None:
        value = int(filters["min_rating"]) if filters["min_rating"].is_integer() else filters["min_rating"]
        active.append({"label": labels["rating"].format(value=value), "url": build_query_url(search_query, filters, ("min_rating", str(filters["min_rating"])), base_path, extra)})
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



CATEGORY_INFO = CATEGORIES

COLLECTION_INFO = {
    "free-tools": {"name": "Free Tools", "description": "Tools with a fully free pricing model."},
    "open-source": {"name": "Open Source", "description": "Software whose source code can be inspected and improved."},
    "low-end-pc": {"name": "Low-end PC", "description": "Lightweight tools suitable for modest hardware."},
    "students": {"name": "For Students", "description": "Accessible tools suited to learning and student workflows."},
    "editor-choice": {"name": "Editor Choices", "description": "Strong all-round tools selected by AtlasFind editorial rules."},
}

COLLECTION_INFO_TR = {
    "free-tools": {"name": "Ücretsiz Araçlar", "description": "Tamamen ücretsiz fiyatlandırma modeline sahip araçlar."},
    "open-source": {"name": "Açık Kaynak", "description": "Kaynak kodu incelenebilen ve geliştirilebilen yazılımlar."},
    "low-end-pc": {"name": "Düşük Donanımlı Bilgisayarlar", "description": "Mütevazı donanımlara uygun, hafif araçlar."},
    "students": {"name": "Öğrenciler İçin", "description": "Öğrenme ve öğrenci iş akışlarına uygun, erişilebilir araçlar."},
    "editor-choice": {"name": "Editörün Seçtikleri", "description": "AtlasFind editoryal ölçütleriyle seçilen güçlü ve çok yönlü araçlar."},
}

def localized_collections(locale):
    return COLLECTION_INFO_TR if locale == "tr" else COLLECTION_INFO

def slugify_category(name):
    return category_slug(name)

def category_cards(items, locale):
    cards = []
    for slug in CATEGORIES:
        info = localized_category(slug, locale)
        category_tools = [tool for tool in items if category_slug(tool.get("category", "")) == slug]
        info.update({
            "count": len(category_tools),
            "free_count": sum(1 for tool in category_tools if tool.get("pricing_type") == "free"),
            "featured": sort_tools(category_tools, "rating")[:3],
            "subcategories": sorted({tool.get("subcategory") for tool in category_tools if tool.get("subcategory")}),
            "subcategory_links": [{"name": name, "slug": slugify_category(name)} for name in sorted({tool.get("subcategory") for tool in category_tools if tool.get("subcategory")})],
        })
        cards.append(info)
    return cards

def category_landing_data(items, slug, locale):
    info = localized_category(slug, locale)
    subcategory_names = sorted({tool.get("subcategory") for tool in items if tool.get("subcategory")})
    subcategory_cards = []
    for name in subcategory_names:
        scoped = [tool for tool in items if tool.get("subcategory") == name]
        subcategory_cards.append({
            "name": name,
            "slug": slugify_category(name),
            "count": len(scoped),
            "free_count": sum(1 for tool in scoped if tool.get("pricing_type") == "free"),
            "ai_count": sum(1 for tool in scoped if tool.get("ai_powered")),
            "featured": sort_tools(scoped, "popular")[:3],
        })
    featured = sort_tools(items, "popular")[:4]
    return {
        **info,
        "count": len(items),
        "subcategory_count": len(subcategory_cards),
        "free_count": sum(1 for tool in items if tool.get("pricing_type") == "free"),
        "open_source_count": sum(1 for tool in items if tool.get("open_source")),
        "ai_count": sum(1 for tool in items if tool.get("ai_powered")),
        "subcategory_cards": subcategory_cards,
        "featured": featured,
        "compare_slugs": [tool.get("slug") for tool in featured[:2]],
    }

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

def paginate(items, page, per_page=24):
    total = len(items)
    pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, pages))
    start = (page - 1) * per_page
    return items[start:start + per_page], {
        "page": page, "pages": pages, "total": total,
        "per_page": per_page, "has_prev": page > 1, "has_next": page < pages,
    }


def pagination_window(page, pages, radius=2):
    if pages <= 7:
        return list(range(1, pages + 1))
    values = {1, pages}
    values.update(range(max(2, page - radius), min(pages, page + radius) + 1))
    output = []
    previous = None
    for value in sorted(values):
        if previous is not None and value - previous > 1:
            output.append(None)
        output.append(value)
        previous = value
    return output

def discovery_context(items, title, description, page_type):
    source_items = list(items)
    filters = parse_filters(request.args)
    selected_category = filters.get("category", "")
    search_query = request.args.get("q", "").strip()[:160]

    search_meta = {"corrected_query": "", "did_correct": False, "duration_ms": 0, "result_count": len(source_items), "detected_needs": []}
    relevance_scores = {}
    if search_query:
        ranked, search_meta = rank_tools(source_items, search_query)
        source_items = [entry["tool"] for entry in ranked]
        relevance_scores = {str(entry["tool"].get("slug") or entry["tool"].get("id")): entry for entry in ranked}
        app.logger.info(
            "catalog_search query=%r tools=%s results=%s duration_ms=%s",
            search_query, len(items), search_meta["result_count"], search_meta["duration_ms"],
        )

    category_scoped_items = source_items
    if selected_category:
        category_scoped_items = [tool for tool in source_items if tool.get("category") == selected_category]

    subcategory = request.args.get("subcategory", "").strip()
    filtered_items = filter_tools(source_items, filters)
    if subcategory:
        filtered_items = [tool for tool in filtered_items if tool.get("subcategory") == subcategory]

    requested_sort = request.args.get("sort", "").strip()
    sort_key = requested_sort or ("relevance" if search_query else "popular")
    if sort_key != "relevance":
        filtered_items = sort_tools(filtered_items, sort_key)

    try:
        page = int(request.args.get("page", "1"))
    except ValueError:
        page = 1
    page_items, pagination = paginate(filtered_items, page)

    categories = sorted({tool.get("category") for tool in (list(items) if search_query else source_items) if tool.get("category")})
    subcategories = sorted({tool.get("subcategory") for tool in category_scoped_items if tool.get("subcategory")})
    base_path = request.path
    persistent = {"sort": sort_key}
    if subcategory:
        persistent["subcategory"] = subcategory
    active_filters = build_active_filters(search_query, filters, base_path, get_locale(), persistent)

    def page_url(target_page):
        extras = dict(persistent)
        extras["page"] = target_page
        return build_query_url(search_query, filters, base_path=base_path, extra=extras)

    page_links = [
        {"page": value, "url": page_url(value) if value is not None else None, "current": value == pagination["page"]}
        for value in pagination_window(pagination["page"], pagination["pages"])
    ]
    corrected_query = search_meta.get("corrected_query", "")
    corrected_query_url = build_query_url(corrected_query, filters, base_path=base_path, extra={"sort": "relevance"}) if search_meta.get("did_correct") else None

    return dict(
        tools=page_items,
        title=title,
        description=description,
        page_type=page_type,
        filters=filters,
        sort_key=sort_key,
        search_query=search_query,
        search_meta=search_meta,
        corrected_query_url=corrected_query_url,
        relevance_scores=relevance_scores,
        subcategory=subcategory,
        categories=categories,
        subcategories=subcategories,
        active_filters=active_filters,
        active_filter_count=len(active_filters) + (1 if subcategory else 0) + (1 if search_query else 0),
        pagination=pagination,
        page_links=page_links,
        previous_page_url=page_url(pagination["page"] - 1) if pagination["has_prev"] else None,
        next_page_url=page_url(pagination["page"] + 1) if pagination["has_next"] else None,
        clear_filters_url=base_path,
        clear_filters_keep_query_url=build_query_url(search_query, {"category": "", "pricing": [], "platforms": [], "system_levels": [], "open_source": False, "offline": False, "ai": False, "turkish": False, "max_ram": None, "min_rating": None}, base_path=base_path, extra={"sort": "relevance"}) if search_query else base_path,
        remove_query_url=build_query_url("", filters, base_path=base_path, extra={"sort": "popular", **({"subcategory": subcategory} if subcategory else {})}),
        subcategory_remove_url=build_query_url(search_query, filters, base_path=base_path, extra={"sort": sort_key}),
        query_args=request.args,
    )


@app.before_request
def resolve_request_locale():
    g.request_id = new_request_id()
    g.csp_nonce = new_request_id()
    validate_request_host()
    enforce_safe_method()
    enforce_api_rate_limit()
    locale = (request.view_args or {}).get("locale")
    if locale is not None and locale not in SUPPORTED_LOCALES:
        abort(404)
    g.locale = ("tr" if request.path.startswith("/admin") else DEFAULT_LOCALE) if locale not in SUPPORTED_LOCALES else locale


@app.url_defaults
def inject_locale_into_urls(endpoint, values):
    if "locale" in values or not request:
        return
    rules = app.url_map._rules_by_endpoint.get(endpoint, ())
    if any("locale" in rule.arguments for rule in rules):
        values["locale"] = get_locale()


def _locale_redirect(locale):
    if locale is not None:
        return None
    endpoint = request.endpoint
    values = dict(request.view_args or {})
    values["locale"] = DEFAULT_LOCALE
    target = url_for(endpoint, **values)
    if request.query_string:
        target += "?" + request.query_string.decode("utf-8")
    return redirect(target, code=301)


@app.after_request
def response_headers(response):
    """Apply caching policy and production security headers."""
    if request.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    elif request.path in {"/robots.txt", "/sitemap.xml"}:
        response.headers["Cache-Control"] = "public, max-age=3600"
    elif request.method == "GET" and response.status_code == 200 and not request.path.startswith("/admin"):
        response.headers.setdefault("Cache-Control", "public, max-age=60, stale-while-revalidate=300")
    if (request.method == "GET" and response.status_code == 200 and request.endpoint
            and not request.path.startswith(("/admin", "/static/", "/api/"))
            and request.path not in {"/robots.txt", "/sitemap.xml", "/favicon.ico"}
            and "bot" not in request.headers.get("User-Agent", "").lower()):
        visitor_id = session.get("visitor_id")
        if not visitor_id:
            visitor_id = uuid.uuid4().hex
            session["visitor_id"] = visitor_id
        country = "Local" if request.remote_addr in {"127.0.0.1", "::1"} else "Unknown"
        if app.config.get("TRUST_PROXY_HEADERS"):
            country = request.headers.get("CF-IPCountry") or request.headers.get("X-Country-Code") or country
        record_visit(visitor_id, client_ip(), country, request.path, request.headers.get("User-Agent", ""))
    return add_security_headers(response)


@app.context_processor
def inject_app_metadata():
    return {
        "app_version": APP_VERSION,
        "site_url": SITE_URL,
        "contact_email": CONTACT_EMAIL,
        "json_ld": json_ld,
        "locale": get_locale(),
        "supported_locales": SUPPORTED_LOCALES,
        "t": translate,
        "localized_path": localized_path,
        "category_slug": category_slug,
        "alternate_urls": alternate_urls(request.path),
        "csp_nonce": getattr(g, "csp_nonce", ""),
        "js_i18n": {key: translate(key) for key in (
            "js.theme.dark", "js.theme.light", "js.menu.open", "js.menu.close",
            "js.loading", "js.copy.success", "js.copy.prompt",
            "js.suggestion.tool", "js.suggestion.search"
        )},
    }

@app.route("/")
@app.route("/<locale>/")
def home(locale=None):
    if (response := _locale_redirect(locale)) is not None:
        return response
    all_tools = load_tools()
    search_query = request.args.get("q", "").strip()[:160]
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
    if not search_query and not active_filters:
        ranked_tools = ranked_tools[:6]
        tools = tools[:6]
    alternatives = alternative_queries(
        search_query,
        search_meta.get("corrected_query", search_query),
        search_meta.get("detected_needs", []),
    ) if search_query and not tools else []

    popular_tools = sort_tools(all_tools, "popular")[:6]
    newest_tools = sort_tools(all_tools, "newest")[:6]
    editor_tools = [tool for tool in sort_tools(all_tools, "rating") if tool.get("editor_choice")][:6]
    spotlight_tools = editor_tools or [tool for tool in popular_tools if tool.get("quality_status") == "verified"][:6] or popular_tools

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
        clear_filters_url=localized_path(f"/?{urlencode({'q': search_query})}" if search_query else "/"),
        total_tool_count=len(all_tools),
        category_count=len(CATEGORIES),
        result_count=len(tools),
        categories=category_cards(all_tools, get_locale()),
        popular_tools=popular_tools,
        newest_tools=newest_tools,
        editor_tools=editor_tools,
        spotlight_tools=spotlight_tools,
        collections=localized_collections(get_locale()),
        seo=page_seo(
            "Yazılımları Keşfet ve Karşılaştır" if get_locale() == "tr" else "Discover and Compare Software",
            "İhtiyacına, bütçene, platformuna ve bilgisayarına uygun yazılımları keşfet ve karşılaştır." if get_locale() == "tr" else "Discover, compare and find software that fits your workflow, platform, budget and hardware.",
            "/",
            robots="noindex,follow" if search_query or any(active_filters) else "index,follow",
        ),
        schemas=[website_schema()],
        breadcrumbs=[],
    )


@app.route("/api/search-suggestions")
def search_suggestions_api():
    query = request.args.get("q", "").strip()[:160]
    return jsonify(search_suggestions(load_tools(), query))



@app.route("/tools")
@app.route("/<locale>/tools")
def tools_directory(locale=None):
    if (response := _locale_redirect(locale)) is not None:
        return response
    items = load_tools()
    title = "Tüm Araçlar" if get_locale() == "tr" else "All Tools"
    description = (
        "AtlasFind kataloğundaki yazılım ve servisleri kategori, platform, fiyatlandırma ve sistem gereksinimlerine göre keşfedin."
        if get_locale() == "tr"
        else "Explore software and services in the AtlasFind catalog by category, platform, pricing and system requirements."
    )
    crumbs = build_breadcrumbs([(("Ana Sayfa" if get_locale() == "tr" else "Home"), "/"), (title, "/tools")])
    return render_template(
        "discovery.html",
        **discovery_context(items, title, description, "catalog"),
        active_page="tools", related_guides=[],
        seo=page_seo(title, description, "/tools"),
        breadcrumbs=crumbs, schemas=[breadcrumb_schema(crumbs)],
    )

@app.route("/categories")
@app.route("/<locale>/categories")
def categories_directory(locale=None):
    if (response := _locale_redirect(locale)) is not None:
        return response
    current_locale = get_locale()
    all_tools = load_tools()
    cards = category_cards(all_tools, current_locale)
    title = "Kategoriler" if current_locale == "tr" else "Categories"
    description = ("AtlasFind araçlarını kullanım alanına göre keşfedin." if current_locale == "tr" else "Explore AtlasFind tools by purpose and category.")
    crumbs = build_breadcrumbs([(("Ana Sayfa" if current_locale == "tr" else "Home"), "/"), (title, "/categories")])
    return render_template(
        "categories.html", categories=cards, active_page="categories",
        category_total=len(cards),
        subcategory_total=len({tool.get("subcategory") for tool in all_tools if tool.get("subcategory")}),
        tool_total=len(all_tools),
        title=title, description=description,
        seo=page_seo(title, description, "/categories"), breadcrumbs=crumbs,
        schemas=[breadcrumb_schema(crumbs)],
    )

@app.route("/categories/<slug>")
@app.route("/<locale>/categories/<slug>")
def category_page(slug, locale=None):
    if (response := _locale_redirect(locale)) is not None:
        return response
    if slug not in CATEGORIES: abort(404)
    current_locale = get_locale()
    info = localized_category(slug, current_locale)
    items=[t for t in load_tools() if category_slug(t.get("category",""))==slug]
    related_guides = [article for article in load_articles() if article.get("category") == slug]
    home_label = "Ana Sayfa" if current_locale == "tr" else "Home"
    categories_label = "Kategoriler" if current_locale == "tr" else "Categories"
    crumbs = build_breadcrumbs([(home_label, "/"), (categories_label, "/categories"), (info["name"], f"/categories/{slug}")])
    context = discovery_context(items, info["name"], info["description"], "category")
    context["category_landing"] = category_landing_data(items, slug, current_locale)
    return render_template(
        "discovery.html", **context,
        active_page="categories", related_guides=related_guides,
        seo=page_seo((f"En İyi {info['name']} Araçları" if current_locale == "tr" else f"Best {info['name']} Tools"), info["description"], f"/categories/{slug}"),
        breadcrumbs=crumbs, schemas=[breadcrumb_schema(crumbs)],
    )

@app.route("/categories/<category_slug_value>/<subcategory_slug>")
@app.route("/<locale>/categories/<category_slug_value>/<subcategory_slug>")
def subcategory_page(category_slug_value, subcategory_slug, locale=None):
    if (response := _locale_redirect(locale)) is not None:
        return response
    if category_slug_value not in CATEGORIES: abort(404)
    current_locale = get_locale()
    category_info = localized_category(category_slug_value, current_locale)
    category_tools = [t for t in load_tools() if category_slug(t.get("category", "")) == category_slug_value]
    subcategories = {slugify_category(t.get("subcategory", "")): t.get("subcategory") for t in category_tools if t.get("subcategory")}
    subcategory_name = subcategories.get(subcategory_slug)
    if not subcategory_name: abort(404)
    items = [t for t in category_tools if t.get("subcategory") == subcategory_name]
    title = subcategory_name
    description = ((f"{category_info['name']} kategorisindeki {subcategory_name} araçlarını keşfedin ve karşılaştırın.") if current_locale == "tr" else f"Discover and compare {subcategory_name} tools in {category_info['name']}.")
    home_label = "Ana Sayfa" if current_locale == "tr" else "Home"
    categories_label = "Kategoriler" if current_locale == "tr" else "Categories"
    crumbs = build_breadcrumbs([(home_label, "/"), (categories_label, "/categories"), (category_info["name"], f"/categories/{category_slug_value}"), (title, f"/categories/{category_slug_value}/{subcategory_slug}")])
    return render_template(
        "discovery.html", **discovery_context(items, title, description, "subcategory"),
        active_page="categories", related_guides=[],
        seo=page_seo(title, description, f"/categories/{category_slug_value}/{subcategory_slug}"),
        breadcrumbs=crumbs, schemas=[breadcrumb_schema(crumbs)],
    )

@app.route("/collections/<slug>")
@app.route("/<locale>/collections/<slug>")
def collection_page(slug, locale=None):
    if (response := _locale_redirect(locale)) is not None:
        return response
    info=localized_collections(get_locale()).get(slug)
    if not info: abort(404)
    items=[t for t in load_tools() if slug in t.get("collections",[])]
    home_label = translate("common.home")
    collections_label = translate("common.collections")
    crumbs = build_breadcrumbs([(home_label, "/"), (collections_label, None), (info["name"], f"/collections/{slug}")])
    return render_template(
        "discovery.html",
        **discovery_context(items, info["name"], info["description"], "collection"),
        active_page="categories", related_guides=[],
        seo=page_seo(info["name"], info["description"], f"/collections/{slug}"),
        breadcrumbs=crumbs, schemas=[breadcrumb_schema(crumbs)],
    )



@app.route("/guides")
@app.route("/<locale>/guides")
def guides(locale=None):
    if (response := _locale_redirect(locale)) is not None:
        return response
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
        content_type_labels={
            "best-tools": translate("guides.type.best_tools"), "alternatives": translate("guides.type.alternatives"),
            "guide": translate("guides.type.guide"), "category-guide": translate("guides.type.category_guide"),
        },
        article_category_labels={
            "design": translate("guides.category.design"), "video": translate("guides.category.video"),
            "office": translate("guides.category.office"), "browser": translate("guides.category.browser"),
            "education": translate("guides.category.education"),
        },
        seo=page_seo(translate("guides.seo_title"), translate("guides.seo_description"), "/guides", robots="noindex,follow" if content_type or category else "index,follow"),
        breadcrumbs=(crumbs := build_breadcrumbs([(translate("common.home"), "/"), (translate("nav.guides"), "/guides")])),
        schemas=[breadcrumb_schema(crumbs)],
    )


@app.route("/guides/<slug>")
@app.route("/<locale>/guides/<slug>")
def article_detail(slug, locale=None):
    if (response := _locale_redirect(locale)) is not None:
        return response
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
        category_info=(localized_category(article.get("category"), get_locale()) if article.get("category") in CATEGORIES else None),
        freshness=content_freshness(article.get("updated_at")),
        seo=page_seo(article.get("title", "Guide"), article.get("description", ""), f"/guides/{slug}", page_type="article"),
         breadcrumbs=(crumbs := build_breadcrumbs([(translate("common.home"), "/"), (translate("nav.guides"), "/guides"), (article.get("title", translate("nav.guides")), f"/guides/{slug}")])),
        schemas=[item for item in [article_schema(article), faq_schema(article.get("faq", [])), breadcrumb_schema(crumbs)] if item],
    )

@app.route("/recommend")
@app.route("/<locale>/recommend")
def recommend(locale=None):
    if (response := _locale_redirect(locale)) is not None:
        return response
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
        seo=page_seo(translate("recommend.seo_title"), translate("recommend.seo_description"), "/recommend", robots="noindex,follow" if submitted else "index,follow"),
        breadcrumbs=build_breadcrumbs([(translate("common.home"), "/"), (translate("nav.recommend"), "/recommend")]), schemas=[],
    )


@app.route("/rating-methodology")
@app.route("/<locale>/rating-methodology")
@app.route("/tr/puanlama-metodolojisi", defaults={"locale": "tr"})
@app.route("/en/rating-methodology", defaults={"locale": "en"})
def rating_methodology(locale=None):
    if (response := _locale_redirect(locale)) is not None:
        return response
    locale_code = get_locale()
    title = translate("rating.methodology_title")
    description = translate("rating.methodology_description")
    canonical = "/tr/puanlama-metodolojisi" if locale_code == "tr" else "/en/rating-methodology"
    crumbs = build_breadcrumbs([(translate("common.home"), localized_path("/", locale_code)), (title, canonical)])
    return render_template("rating_methodology.html", active_page="methodology", seo=page_seo(title, description, canonical), breadcrumbs=crumbs, schemas=[breadcrumb_schema(crumbs)])

@app.route("/tools/<slug>")
@app.route("/<locale>/tools/<slug>")
def tool_detail(slug, locale=None):
    if (response := _locale_redirect(locale)) is not None:
        return response
    tool = find_tool_by_slug(slug)

    if tool is None:
        abort(404)

    alternatives = find_alternatives(
        tool,
        limit=6
    )

    locale_code = get_locale()
    title = translate("tool.seo_title", name=tool.get("name", "Tool"))
    description = translate("tool.seo_description", name=tool.get("name", "Tool"))
    canonical_path = f"/{locale_code}/tools/{slug}"
    crumbs = build_breadcrumbs([
        (translate("common.home"), localized_path("/", locale_code)),
        (translate("nav.tools"), localized_path("/tools", locale_code)),
        (tool.get("name", "Tool"), canonical_path),
    ])

    rating_payload = dict(tool.get("rating_v103") or {})
    rating_payload["user_rating"] = aggregate_user_rating(slug)
    tool = {**tool, "rating_v103": rating_payload}
    rating_csrf_token = session.get("rating_csrf_token")
    if not rating_csrf_token:
        rating_csrf_token = secrets.token_urlsafe(32)
        session["rating_csrf_token"] = rating_csrf_token

    return render_template(
        "tool.html",
        tool=tool,
        rating_csrf_token=rating_csrf_token,
        alternatives=alternatives,
        freshness=tool_freshness(tool),
        seo=page_seo(title, description, canonical_path),
        breadcrumbs=crumbs,
        schemas=[software_schema(tool), breadcrumb_schema(crumbs)],
    )


@app.post("/tools/<slug>/rate")
@app.post("/<locale>/tools/<slug>/rate")
def rate_tool(slug, locale=None):
    if (response := _locale_redirect(locale)) is not None:
        return response
    if find_tool_by_slug(slug) is None:
        abort(404)

    submitted_csrf = str(request.form.get("csrf_token") or "")
    expected_csrf = str(session.get("rating_csrf_token") or "")
    if not expected_csrf or not secrets.compare_digest(submitted_csrf, expected_csrf):
        abort(400)

    try:
        score = float(request.form.get("score", ""))
    except (TypeError, ValueError):
        abort(400)
    if score < 1 or score > 10:
        abort(400)

    voter_token = session.get("rating_voter_token")
    if not voter_token:
        voter_token = secrets.token_urlsafe(32)
        session["rating_voter_token"] = voter_token
    user_key = anonymous_user_key(app.config["SECRET_KEY"], voter_token)
    upsert_review(
        tool_slug=slug,
        user_key_hash=user_key,
        score=score,
        criteria={},
        comment="",
        risk_score=0,
        status="verified",
    )
    return redirect(url_for("tool_detail", locale=get_locale(), slug=slug, rating_saved="1") + "#community-rating")


def _comparison_value(tool, key):
    current_locale = get_locale()
    unknown = translate("common.unknown")
    yes = translate("common.yes")
    no = translate("common.no")
    if key in {"open_source", "offline", "ai_powered"}:
        return yes if tool.get(key) else no
    if key == "minimum_ram_gb":
        value = tool.get(key)
        return f"{value:g} GB" if isinstance(value, (int, float)) and not isinstance(value, bool) else unknown
    if key == "platforms":
        return ", ".join(tool.get("platforms") or []) or unknown
    if key == "languages":
        values = tool.get("languages") or []
        return ", ".join(value.upper() for value in values) or unknown
    if key == "rating":
        rating = tool.get("rating_v103") or {}
        value = rating.get("overall_score")
        return f"{value:.1f} / 10" if isinstance(value, (int, float)) else translate("tool.not_rated")
    if key == "target_users":
        return ", ".join(tool.get("target_users") or []) or unknown
    if key == "pricing":
        pricing_key = str(tool.get("pricing_type") or tool.get("pricing") or "").strip().lower()
        return translate(f"pricing.{pricing_key}") if pricing_key else unknown
    return str(tool.get(key) or unknown)


def build_comparison_rows(tools):
    definitions = [
        ("compare.row.category", "category"),
        ("compare.row.pricing", "pricing"),
        ("compare.row.open_source", "open_source"),
        ("compare.row.offline", "offline"),
        ("compare.row.ai", "ai_powered"),
        ("compare.row.platforms", "platforms"),
        ("compare.row.ram", "minimum_ram_gb"),
        ("compare.row.system", "system_level"),
        ("compare.row.languages", "languages"),
        ("compare.row.rating", "rating"),
        ("compare.row.target_users", "target_users"),
    ]
    rows = []
    for label_key, key in definitions:
        values = [_comparison_value(tool, key) for tool in tools]
        rows.append({"label": translate(label_key), "key": key, "values": values, "common": len(set(values)) <= 1})
    return rows


def _localized_recommendation_result(result):
    """Return recommendation text that never leaks the other locale into the page."""
    tool = result["tool"]
    reasons = []
    concerns = []
    for reason in result.get("reasons", []):
        if get_locale() == "tr":
            replacements = {
                "Category fit:": "Kategori uyumu:", "Relevant capabilities:": "İlgili yetenekler:",
                "Platform fit:": "Platform uyumu:", "Budget fit:": "Bütçe uyumu:",
                "Hardware fit:": "Donanım uyumu:", "Experience fit:": "Deneyim uyumu:",
                "Privacy fit:": "Gizlilik uyumu:", "Offline fit:": "Çevrimdışı kullanım:",
            }
            for source, target in replacements.items():
                reason = reason.replace(source, target)
        reasons.append(reason)
    for concern in result.get("concerns", []):
        if get_locale() == "tr":
            replacements = {
                "Purpose mismatch:": "Amaç uyumsuzluğu:", "Platform limitation:": "Platform sınırlaması:",
                "Budget mismatch:": "Bütçe uyumsuzluğu:", "Hardware concern:": "Donanım uyarısı:",
                "Learning-curve concern:": "Öğrenme eğrisi uyarısı:", "Privacy mismatch:": "Gizlilik uyumsuzluğu:",
                "Offline limitation:": "Çevrimdışı kullanım sınırlaması:",
            }
            for source, target in replacements.items():
                concern = concern.replace(source, target)
        concerns.append(concern)
    return {**result, "tool": tool, "reasons": reasons, "concerns": concerns}


@app.route("/compare")
@app.route("/<locale>/compare")
def compare_tools(locale=None):
    if (response := _locale_redirect(locale)) is not None:
        return response

    requested_slugs = [slug.strip() for slug in request.args.getlist("tools") if slug and slug.strip()]
    if not requested_slugs:
        requested_slugs = [request.args.get("left", "").strip(), request.args.get("right", "").strip()]
        requested_slugs = [slug for slug in requested_slugs if slug]

    unique_slugs = []
    duplicate_removed = False
    for slug in requested_slugs:
        if slug in unique_slugs:
            duplicate_removed = True
            continue
        unique_slugs.append(slug)
    unique_slugs = unique_slugs[:4]

    selected_tools = []
    invalid_slugs = []
    for slug in unique_slugs:
        tool = find_tool_by_slug(slug, get_locale())
        if tool is None:
            invalid_slugs.append(slug)
            continue
        selected_tools.append(tool)

    category_mismatch_removed = False
    comparison_category_slug = None
    if selected_tools:
        comparison_category_slug = category_slug(selected_tools[0].get("category", ""))
        category_scoped_tools = [selected_tools[0]]
        for tool in selected_tools[1:]:
            if category_slug(tool.get("category", "")) == comparison_category_slug:
                category_scoped_tools.append(tool)
            else:
                category_mismatch_removed = True
        selected_tools = category_scoped_tools

    current_locale = get_locale()
    all_comparison_tools = sorted(load_tools(current_locale), key=lambda tool: str(tool.get("name", "")).casefold())
    comparison_category = localized_category(comparison_category_slug, current_locale) if comparison_category_slug in CATEGORIES else None

    hide_common = request.args.get("hide_common") == "1"
    rows = build_comparison_rows(selected_tools) if len(selected_tools) >= 2 else []
    visible_rows = [row for row in rows if not (hide_common and row["common"])]

    preferences = parse_recommendation_preferences(request.args)
    preference_submitted = recommendation_requested(preferences)
    scored_tools = [_localized_recommendation_result(score_recommendation(tool, preferences)) for tool in selected_tools] if preference_submitted else []
    scored_tools.sort(key=lambda item: (item["match"], item["score"], item["tool"].get("rating", 0)), reverse=True)
    winner = scored_tools[0] if scored_tools else None

    title = translate("compare.seo_title")
    description = translate("compare.seo_description")
    home_label = translate("common.home")
    compare_label = translate("nav.compare")
    crumbs = build_breadcrumbs([(home_label, "/"), (compare_label, "/compare")])

    return render_template(
        "compare.html",
        selected_tools=selected_tools,
        selected_slugs=[tool.get("slug") for tool in selected_tools],
        comparison_rows=visible_rows,
        all_rows=rows,
        hide_common=hide_common,
        all_tools=all_comparison_tools,
        comparison_category_slug=comparison_category_slug,
        comparison_category=comparison_category,
        category_mismatch_removed=category_mismatch_removed,
        preferences=preferences,
        purpose_options=RECOMMENDATION_PURPOSES,
        preference_submitted=preference_submitted,
        scored_tools=scored_tools,
        winner=winner,
        duplicate_removed=duplicate_removed,
        invalid_slugs=invalid_slugs,
        seo=page_seo(title, description, "/compare", robots="noindex,follow"),
        breadcrumbs=crumbs,
        schemas=[breadcrumb_schema(crumbs)],
    )


@app.route("/health")
def health_check():
    """Lightweight liveness endpoint for hosting health checks."""
    return jsonify({
        "status": "ok",
        "service": "atlasfind",
        "version": APP_VERSION,
    })


@app.route("/ready")
def readiness_check():
    """Verify that SQLite is reachable and the catalog has been seeded."""
    import sqlite3

    try:
        connection = sqlite3.connect(DATABASE_PATH)
        integrity = connection.execute("PRAGMA quick_check").fetchone()[0]
        tool_count = connection.execute("SELECT COUNT(*) FROM tools").fetchone()[0]
        translation_count = connection.execute("SELECT COUNT(*) FROM tool_translations").fetchone()[0]
        category_count = connection.execute("SELECT COUNT(DISTINCT category_id) FROM tools WHERE COALESCE(status,'published')='published'").fetchone()[0]
        connection.close()
    except Exception:
        app.logger.exception("readiness_check_failed")
        return jsonify({"status": "not_ready", "database": "unavailable"}), 503

    ready = integrity == "ok" and tool_count >= 700 and translation_count >= tool_count * 2 and category_count == 18
    return jsonify({
        "status": "ready" if ready else "not_ready",
        "database": "ok" if integrity == "ok" else "corrupt",
        "tools": tool_count,
        "translations": translation_count,
        "categories": category_count,
        "version": APP_VERSION,
    }), 200 if ready else 503


@app.route("/robots.txt")
def robots_txt():
    body = "\n".join([
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /api/",
        f"Sitemap: {absolute_url('/sitemap.xml')}",
        "",
    ])
    return Response(body, mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap_xml():
    from xml.sax.saxutils import escape

    base_urls = [("/", None), ("/tools", None), ("/categories", None), ("/guides", None), ("/recommend", None), ("/about", None), ("/collaborate", None), ("/privacy", None), ("/terms", None), ("/cookies", None), ("/contact", None)]
    base_urls.extend((f"/tools/{tool.get('slug')}", (tool.get('freshness') or {}).get('last_updated_at') or tool.get('date_added')) for tool in load_tools(DEFAULT_LOCALE))
    base_urls.extend((f"/guides/{article.get('slug')}", article.get('updated_at') or article.get('published_at')) for article in load_articles(DEFAULT_LOCALE))
    base_urls.extend((f"/categories/{slug}", None) for slug in CATEGORIES)
    base_urls.extend((f"/collections/{slug}", None) for slug in COLLECTION_INFO)
    urls = [(localized_path(path, locale), lastmod) for locale in SUPPORTED_LOCALES for path, lastmod in base_urls]

    seen = set()
    entries = []
    for path, lastmod in urls:
        if path in seen:
            continue
        seen.add(path)
        loc = escape(absolute_url(path))
        lastmod_xml = f"<lastmod>{escape(str(lastmod))}</lastmod>" if lastmod else ""
        entries.append(f"<url><loc>{loc}</loc>{lastmod_xml}</url>")

    xml = '<?xml version="1.0" encoding="UTF-8"?>' + \
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + \
          ''.join(entries) + '</urlset>'
    return Response(xml, mimetype="application/xml")



@app.route("/privacy", strict_slashes=False)
@app.route("/<locale>/privacy", strict_slashes=False)
def privacy(locale=None):
    return _public_page("privacy", locale)

@app.route("/about", strict_slashes=False)
@app.route("/<locale>/about", strict_slashes=False)
def about(locale=None):
    return _public_page("about", locale)

@app.route("/collaborate", strict_slashes=False)
@app.route("/<locale>/collaborate", strict_slashes=False)
def collaborate(locale=None):
    return _public_page("collaborate", locale)

@app.route("/terms", strict_slashes=False)
@app.route("/<locale>/terms", strict_slashes=False)
def terms(locale=None):
    return _public_page("terms", locale)

@app.route("/cookies", strict_slashes=False)
@app.route("/<locale>/cookies", strict_slashes=False)
def cookies(locale=None):
    return _public_page("cookies", locale)

@app.route("/contact", strict_slashes=False)
@app.route("/<locale>/contact", strict_slashes=False)
def contact(locale=None):
    return _public_page("contact", locale)

def _public_page(page_key, locale=None):
    if (response := _locale_redirect(locale)) is not None:
        return response
    content = PUBLIC_PAGES[page_key][get_locale()]
    path = f"/{get_locale()}/{page_key}"
    return render_template(
        "public_page.html", content=content, page_key=page_key, active_page=page_key,
        seo=page_seo(content["title"], content["description"], path),
        breadcrumbs=build_breadcrumbs([(translate("common.home"), url_for("home")), (content["title"], None)]),
        schemas=[], tool_total=len(load_tools()),
    )

@app.route("/tool/<slug>")
def legacy_tool_url(slug):
    return redirect(localized_path(f"/tools/{slug}", DEFAULT_LOCALE), code=301)


@app.route("/category/<slug>")
def legacy_category_url(slug):
    return redirect(localized_path(f"/categories/{slug}", DEFAULT_LOCALE), code=301)


@app.route("/guide/<slug>")
def legacy_guide_url(slug):
    return redirect(localized_path(f"/guides/{slug}", DEFAULT_LOCALE), code=301)


@app.errorhandler(400)
def bad_request(error):
    app.logger.warning("bad_request request_id=%s path=%s", getattr(g, "request_id", "-"), request.path)
    title = translate("errors.400.title")
    message = translate("errors.400.text")
    return render_template(
        "error.html", status_code=400, title=title,
        message=message, request_id=getattr(g, "request_id", None),
        seo=page_seo(title, message, request.path, robots="noindex,nofollow"),
        breadcrumbs=[], schemas=[],
    ), 400


@app.errorhandler(405)
def method_not_allowed(error):
    title = translate("errors.405.title")
    message = translate("errors.405.text")
    return render_template(
        "error.html", status_code=405, title=title,
        message=message, request_id=getattr(g, "request_id", None),
        seo=page_seo(title, message, request.path, robots="noindex,nofollow"),
        breadcrumbs=[], schemas=[],
    ), 405


@app.errorhandler(413)
def request_too_large(error):
    title = translate("errors.413.title")
    message = translate("errors.413.text")
    return render_template(
        "error.html", status_code=413, title=title,
        message=message, request_id=getattr(g, "request_id", None),
        seo=page_seo(title, message, request.path, robots="noindex,nofollow"),
        breadcrumbs=[], schemas=[],
    ), 413


@app.errorhandler(429)
def too_many_requests(error):
    title = translate("errors.429.title")
    message = translate("errors.429.text")
    return render_template(
        "error.html", status_code=429, title=title,
        message=message, request_id=getattr(g, "request_id", None),
        seo=page_seo(title, message, request.path, robots="noindex,nofollow"),
        breadcrumbs=[], schemas=[],
    ), 429


@app.errorhandler(500)
def internal_error(error):
    request_id = getattr(g, "request_id", None)
    app.logger.exception("internal_server_error request_id=%s path=%s", request_id, request.path)
    title = translate("errors.500.title")
    message = translate("errors.500.text")
    return render_template(
        "error.html", status_code=500, title=title,
        message=message, request_id=request_id,
        seo=page_seo(title, message, request.path, robots="noindex,nofollow"),
        breadcrumbs=[], schemas=[],
    ), 500


@app.errorhandler(404)
def page_not_found(error):
    first_segment = request.path.strip("/").split("/", 1)[0]
    g.locale = first_segment if first_segment in SUPPORTED_LOCALES else DEFAULT_LOCALE
    popular_tools = sorted(
        load_tools(),
        key=lambda tool: (tool.get("popularity_score", 0), tool.get("rating", 0)),
        reverse=True,
    )[:6]
    crumbs = build_breadcrumbs([(translate("common.home"), "/"), (translate("common.page_not_found"), request.path)])
    return render_template(
        "404.html",
        popular_tools=popular_tools,
        active_page=None,
        seo=page_seo(
            translate("errors.404.title"),
            translate("errors.404.text"),
            request.path,
            robots="noindex,follow",
        ),
        breadcrumbs=crumbs,
        schemas=[breadcrumb_schema(crumbs)],
    ), 404


if __name__ == "__main__":
    debug = os.environ.get("ATLASFIND_DEBUG", "0").strip().lower() in {"1", "true", "yes", "on"}
    if app.config.get("PRODUCTION"):
        debug = False
    app.run(debug=debug)
