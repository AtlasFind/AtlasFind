from __future__ import annotations

import re
import unicodedata


def _slug(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    text = text.lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


CATEGORIES = {
    "artificial-intelligence": {
        "name_en": "Artificial Intelligence", "name_tr": "Yapay Zekâ", "icon": "✦",
        "description_en": "AI assistants, generators, local models and intelligent automation tools.",
        "description_tr": "Yapay zekâ asistanları, üretim araçları, yerel modeller ve akıllı otomasyon çözümleri.",
        "aliases": ["Artificial Intelligence"],
    },
    "development": {
        "name_en": "Development", "name_tr": "Geliştirme", "icon": "</>",
        "description_en": "Editors, IDEs, databases, APIs and utilities for building software.",
        "description_tr": "Yazılım geliştirmek için editörler, IDE'ler, veritabanları, API araçları ve yardımcı uygulamalar.",
        "aliases": ["Development", "Database"],
    },
    "design-and-graphics": {
        "name_en": "Design and Graphics", "name_tr": "Tasarım ve Grafik", "icon": "◇",
        "description_en": "Image editing, illustration, UI design and visual creation tools.",
        "description_tr": "Görsel düzenleme, illüstrasyon, arayüz tasarımı ve görsel üretim araçları.",
        "aliases": ["Design", "Design and Graphics"],
    },
    "video-and-animation": {
        "name_en": "Video and Animation", "name_tr": "Video ve Animasyon", "icon": "▶",
        "description_en": "Video editing, recording, motion graphics and animation software.",
        "description_tr": "Video düzenleme, kayıt, hareketli grafik ve animasyon yazılımları.",
        "aliases": ["Video", "Video and Animation"],
    },
    "audio-and-music": {
        "name_en": "Audio and Music", "name_tr": "Ses ve Müzik", "icon": "♫",
        "description_en": "Audio editing, music production, voice and podcast tools.",
        "description_tr": "Ses düzenleme, müzik üretimi, seslendirme ve podcast araçları.",
        "aliases": ["Audio", "Audio and Music"],
    },
    "cybersecurity": {
        "name_en": "Cybersecurity", "name_tr": "Siber Güvenlik", "icon": "⬡",
        "description_en": "Privacy, network, account and device protection tools.",
        "description_tr": "Gizlilik, ağ, hesap ve cihaz güvenliği araçları.",
        "aliases": ["Security", "Cybersecurity"],
    },
    "productivity": {
        "name_en": "Productivity", "name_tr": "Verimlilik", "icon": "✓",
        "description_en": "Task, workflow, note-taking and personal organization tools.",
        "description_tr": "Görev, iş akışı, not alma ve kişisel düzenleme araçları.",
        "aliases": ["Productivity"],
    },
    "office-and-documents": {
        "name_en": "Office and Documents", "name_tr": "Ofis ve Belgeler", "icon": "▤",
        "description_en": "Documents, spreadsheets, presentations and PDF utilities.",
        "description_tr": "Belge, tablo, sunum ve PDF araçları.",
        "aliases": ["Office", "Office and Documents"],
    },
    "education": {
        "name_en": "Education", "name_tr": "Eğitim", "icon": "⌂",
        "description_en": "Learning, study, language and classroom tools.",
        "description_tr": "Öğrenme, ders çalışma, dil ve sınıf araçları.",
        "aliases": ["Education"],
    },
    "marketing-and-seo": {
        "name_en": "Marketing and SEO", "name_tr": "Pazarlama ve SEO", "icon": "↗",
        "description_en": "SEO, analytics, social media and campaign tools.",
        "description_tr": "SEO, analiz, sosyal medya ve kampanya araçları.",
        "aliases": ["Marketing and SEO"],
    },
    "communication": {
        "name_en": "Communication", "name_tr": "İletişim", "icon": "◌",
        "description_en": "Messaging, meetings, collaboration and community platforms.",
        "description_tr": "Mesajlaşma, toplantı, iş birliği ve topluluk platformları.",
        "aliases": ["Communication"],
    },
    "cloud-and-storage": {
        "name_en": "Cloud and Storage", "name_tr": "Bulut ve Depolama", "icon": "☁",
        "description_en": "Cloud storage, file sync, backup and infrastructure services.",
        "description_tr": "Bulut depolama, dosya eşitleme, yedekleme ve altyapı hizmetleri.",
        "aliases": ["Cloud", "Cloud and Storage"],
    },
    "finance-and-business": {
        "name_en": "Finance and Business", "name_tr": "Finans ve İş", "icon": "₺",
        "description_en": "Accounting, invoicing, business planning and finance tools.",
        "description_tr": "Muhasebe, faturalama, iş planlama ve finans araçları.",
        "aliases": ["Finance and Business"],
    },
    "data-and-analytics": {
        "name_en": "Data and Analytics", "name_tr": "Veri ve Analitik", "icon": "▥",
        "description_en": "Data visualization, business intelligence and analytics tools.",
        "description_tr": "Veri görselleştirme, iş zekâsı ve analiz araçları.",
        "aliases": ["Data and Analytics"],
    },
    "web-and-hosting": {
        "name_en": "Web and Hosting", "name_tr": "Web ve Hosting", "icon": "◎",
        "description_en": "Website building, hosting, deployment and domain tools.",
        "description_tr": "Site oluşturma, hosting, dağıtım ve alan adı araçları.",
        "aliases": ["Web and Hosting"],
    },
    "system-utilities": {
        "name_en": "System Utilities", "name_tr": "Sistem Araçları", "icon": "⚙",
        "description_en": "Maintenance, monitoring, compression and operating system utilities.",
        "description_tr": "Bakım, izleme, sıkıştırma ve işletim sistemi yardımcı araçları.",
        "aliases": ["System Utilities"],
    },
    "browsers-and-internet": {
        "name_en": "Browsers and Internet", "name_tr": "Tarayıcılar ve İnternet", "icon": "◉",
        "description_en": "Web browsers, download managers and internet utilities.",
        "description_tr": "Web tarayıcıları, indirme yöneticileri ve internet yardımcı araçları.",
        "aliases": ["Browser", "Browsers and Internet"],
    },
    "gaming-and-entertainment": {
        "name_en": "Gaming and Entertainment", "name_tr": "Oyun ve Eğlence", "icon": "◆",
        "description_en": "Game platforms, streaming, media and entertainment tools.",
        "description_tr": "Oyun platformları, yayın, medya ve eğlence araçları.",
        "aliases": ["Gaming and Entertainment"],
    },
}

# Category identity must stay language-neutral. Tool translation payloads from
# earlier releases contain both old and new Turkish labels, so every known
# display label resolves to the same canonical category slug.
LEGACY_LOCALIZED_ALIASES = {
    "Yapay Zekâ": "artificial-intelligence",
    "Yapay Zeka": "artificial-intelligence",
    "Geliştirme": "development",
    "Kodlama ve Geliştirme": "development",
    "Veritabanı": "development",
    "Tasarım": "design-and-graphics",
    "Tasarım ve Grafik": "design-and-graphics",
    "Video": "video-and-animation",
    "Video ve Animasyon": "video-and-animation",
    "Ses": "audio-and-music",
    "Ses ve Müzik": "audio-and-music",
    "Güvenlik": "cybersecurity",
    "Siber Güvenlik": "cybersecurity",
    "Üretkenlik": "productivity",
    "Verimlilik": "productivity",
    "Ofis": "office-and-documents",
    "Ofis ve Doküman": "office-and-documents",
    "Ofis ve Belgeler": "office-and-documents",
    "Eğitim": "education",
    "Pazarlama ve SEO": "marketing-and-seo",
    "İletişim": "communication",
    "Bulut": "cloud-and-storage",
    "Bulut ve Depolama": "cloud-and-storage",
    "Finans ve İşletme": "finance-and-business",
    "Finans ve İş": "finance-and-business",
    "Veri ve Analiz": "data-and-analytics",
    "Veri ve Analitik": "data-and-analytics",
    "Web ve Hosting": "web-and-hosting",
    "Sistem Araçları": "system-utilities",
    "Tarayıcı": "browsers-and-internet",
    "Tarayıcılar ve İnternet": "browsers-and-internet",
    "Oyun ve Eğlence": "gaming-and-entertainment",
}

ALIAS_TO_SLUG = {}
for slug, info in CATEGORIES.items():
    for alias in [slug, info["name_en"], info["name_tr"], *info["aliases"]]:
        ALIAS_TO_SLUG[_slug(alias)] = slug
for alias, slug in LEGACY_LOCALIZED_ALIASES.items():
    ALIAS_TO_SLUG[_slug(alias)] = slug


def category_slug(name: str) -> str:
    normalized = _slug(name)
    return ALIAS_TO_SLUG.get(normalized, normalized)


def category_name(slug: str, locale: str = "en") -> str:
    info = CATEGORIES[slug]
    return info["name_tr"] if locale == "tr" else info["name_en"]


def category_description(slug: str, locale: str = "en") -> str:
    info = CATEGORIES[slug]
    return info["description_tr"] if locale == "tr" else info["description_en"]


def localized_category(slug: str, locale: str = "en") -> dict:
    info = CATEGORIES[slug]
    return {
        "slug": slug,
        "name": category_name(slug, locale),
        "description": category_description(slug, locale),
        "icon": info["icon"],
        "canonical_name": info["name_en"],
    }
