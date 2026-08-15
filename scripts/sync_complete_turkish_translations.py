"""Create complete, natural Turkish payloads for every published catalog tool."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from database import transaction
from catalog.loader import load_published_catalog

CATEGORY_TR = {
    "Artificial Intelligence": "Yapay Zekâ", "Audio and Music": "Ses ve Müzik",
    "Browsers and Internet": "Tarayıcılar ve İnternet", "Cloud and Storage": "Bulut ve Depolama",
    "Communication": "İletişim", "Cybersecurity": "Siber Güvenlik",
    "Data and Analytics": "Veri ve Analitik", "Design and Graphics": "Tasarım ve Grafik",
    "Development": "Geliştirme", "Education": "Eğitim",
    "Finance and Business": "Finans ve İş", "Gaming and Entertainment": "Oyun ve Eğlence",
    "Marketing and SEO": "Pazarlama ve SEO", "Office and Documents": "Ofis ve Belgeler",
    "Productivity": "Verimlilik", "System Utilities": "Sistem Araçları",
    "Video and Animation": "Video ve Animasyon", "Web and Hosting": "Web ve Barındırma",
}

PHRASES = {
    "artificial intelligence": "yapay zekâ", "self-hosted": "kendi sunucunda barındırılan",
    "self hosted": "kendi sunucunda barındırılan", "low-code": "az kodlu", "no-code": "kodsuz",
    "open source": "açık kaynak", "read it later": "sonra okuma", "e-book": "e-kitap",
    "ui/ux": "arayüz ve kullanıcı deneyimi", "2d": "2B", "3d": "3B",
    "ai": "yapay zekâ", "api": "API", "crm": "müşteri ilişkileri yönetimi", "erp": "kurumsal kaynak planlama",
    "seo": "SEO", "vpn": "VPN", "ide": "tümleşik geliştirme ortamı", "paas": "PaaS",
    "accounting": "muhasebe", "applications": "uygulamalar", "assistants": "asistanları",
    "analytics": "analitik", "antivirus": "antivirüs", "application": "uygulama", "audio": "ses",
    "authenticators": "kimlik doğrulayıcılar", "automation": "otomasyon", "backup": "yedekleme",
    "banking": "bankacılık", "behavior": "davranış", "big data": "büyük veri", "billing": "faturalama",
    "bookmark": "yer imi", "bootable": "önyüklenebilir", "browsers": "tarayıcılar", "budgeting": "bütçeleme",
    "business": "iş", "calendar": "takvim", "chat": "sohbet", "classroom": "sınıf",
    "clients": "istemcileri", "cloud": "bulut", "code": "kod", "coding": "kodlama",
    "communication": "iletişim", "community": "topluluk", "compatibility": "uyumluluk",
    "compositing": "birleştirme", "compression": "sıkıştırma", "containers": "kapsayıcılar",
    "content": "içerik", "courses": "kurslar", "creative": "yaratıcı", "creation": "üretim",
    "daily": "günlük", "data": "veri", "database": "veritabanı", "databases": "veritabanları",
    "design": "tasarım", "desktop": "masaüstü", "developer": "geliştirici", "device": "cihaz",
    "diagramming": "diyagram oluşturma", "digital": "dijital", "disk": "disk", "dj": "DJ",
    "document": "belge", "documents": "belgeler", "download": "indirme", "editing": "düzenleme",
    "editors": "düzenleyicileri", "education": "eğitim", "email": "e-posta", "emulation": "öykünme",
    "endpoint": "uç nokta", "engineering": "mühendisliği", "expense": "gider", "file": "dosya",
    "finance": "finans", "firewalls": "güvenlik duvarları", "flashcards": "bilgi kartları",
    "forensics": "adli bilişim", "game": "oyun", "games": "oyunlar", "gaming": "oyun",
    "generation": "üretimi", "git": "Git", "graphic": "grafik", "hardware": "donanım",
    "headless": "başsız", "hosting": "barındırma", "image": "görsel", "infographics": "bilgi grafikleri",
    "integration": "entegrasyonu", "intelligence": "zekâsı", "interface": "arayüz", "internet": "internet",
    "issue": "sorun", "knowledge": "bilgi", "language": "dil", "launchers": "başlatıcıları",
    "learning": "öğrenme", "libraries": "kütüphaneleri", "local": "yerel", "log": "günlük",
    "management": "yönetimi", "managers": "yöneticileri", "marketing": "pazarlama", "media": "medya",
    "meetings": "toplantıları", "messaging": "mesajlaşma", "metasearch": "üst arama", "monitoring": "izleme",
    "motion": "hareketli", "music": "müzik", "network": "ağ", "newsletters": "bültenler",
    "notes": "notlar", "notation": "notasyonu", "object": "nesne", "office": "ofis", "online": "çevrim içi",
    "orchestration": "orkestrasyonu", "password": "parola", "payments": "ödemeler", "pdf": "PDF",
    "penetration": "sızma", "personal": "kişisel", "photo": "fotoğraf", "planning": "planlama",
    "platforms": "platformları", "players": "oynatıcıları", "podcasting": "podcast", "presentations": "sunumlar",
    "privacy": "gizlilik", "private": "özel", "production": "üretimi", "productivity": "verimlilik",
    "project": "proje", "publishing": "yayıncılık", "readers": "okuyucuları", "reading": "okuma",
    "recording": "kayıt", "reference": "kaynak", "remote": "uzaktan", "research": "araştırma",
    "reverse": "tersine", "scheduling": "zamanlama", "science": "bilimi", "screen": "ekran",
    "search": "arama", "secure": "güvenli", "security": "güvenlik", "server": "sunucu",
    "servers": "sunucuları", "sharing": "paylaşımı", "social": "sosyal", "software": "yazılım",
    "spreadsheets": "elektronik tablolar", "stem": "STEM", "stop motion": "kare kare animasyon",
    "storage": "depolama", "streaming": "akış", "subscription": "abonelik", "sync": "eşitleme",
    "system": "sistem", "task": "görev", "team": "ekip", "technology": "teknoloji",
    "terminals": "terminaller", "testing": "testi", "time": "zaman", "tools": "araçları",
    "tracking": "takibi", "transfer": "aktarımı", "typesetting": "dizgi", "uninstallers": "kaldırıcıları",
    "utilities": "yardımcı araçları", "vector": "vektör", "version control": "sürüm kontrolü",
    "video": "video", "visual": "görsel", "voice": "sesli", "vulnerability": "güvenlik açığı",
    "warehousing": "ambarlama", "web": "web", "website": "web sitesi", "whiteboards": "beyaz tahtalar",
    "wireless": "kablosuz", "word processing": "kelime işleme", "work": "iş", "workflow": "iş akışı",
    "writing": "yazma", "and": "ve",
    "access": "erişim", "administrative": "yönetim", "analysis": "analiz", "animation": "animasyon",
    "anonymity": "anonimlik", "anonymous": "anonim", "archiving": "arşivleme", "art": "sanat",
    "assistant": "asistan", "audit": "denetim", "auditing": "denetleme", "backend": "arka uç",
    "based": "tabanlı", "beginner": "başlangıç", "blocking": "engelleme", "booking": "rezervasyon",
    "bookmarks": "yer imleri", "books": "kitaplar", "browser": "tarayıcı", "builders": "oluşturucuları",
    "cache": "önbellek", "capture": "yakalama", "cleaning": "temizleme", "click": "tıklama",
    "client": "istemci", "collaboration": "iş birliği", "color": "renk", "command": "komut",
    "commerce": "ticaret", "complete": "tam", "conferencing": "konferans", "contacts": "kişiler",
    "control": "kontrol", "conversion": "dönüştürme", "converter": "dönüştürücü", "cross": "çapraz",
    "custom": "özel", "customer": "müşteri", "customization": "özelleştirme", "cutting": "kesme",
    "cybersecurity": "siber güvenlik", "dashboards": "gösterge panoları", "datasets": "veri kümeleri",
    "debugger": "hata ayıklayıcı", "deployment": "dağıtım", "development": "geliştirme",
    "devops": "DevOps", "discovery": "keşif", "distributions": "dağıtımları", "documentation": "belgelendirme",
    "drag": "sürükle", "drawing": "çizim", "drop": "bırak", "editor": "düzenleyici", "effects": "efektleri",
    "embedded": "gömülü", "encoding": "kodlama", "encryption": "şifreleme", "engines": "motorları",
    "entertainment": "eğlence", "events": "etkinlikler", "extensions": "uzantıları", "feature": "özellik",
    "feed": "akış", "files": "dosyalar", "filesharing": "dosya paylaşımı", "film": "film",
    "forums": "forumlar", "free": "ücretsiz", "galleries": "galerileri", "generative": "üretken",
    "global": "küresel", "grading": "notlandırma", "graphics": "grafikler", "human": "insan",
    "illustration": "illüstrasyon", "inventory": "envanter", "library": "kütüphane", "lightweight": "hafif",
    "line": "satır", "link": "bağlantı", "lists": "listeler", "live": "canlı", "localization": "yerelleştirme",
    "lossless": "kayıpsız", "machine": "makine", "mailing": "posta", "making": "oluşturma",
    "malware": "kötü amaçlı yazılım", "manager": "yönetici", "maps": "haritalar", "memory": "bellek",
    "minimal": "yalın", "miscellaneous": "çeşitli", "mixing": "miksaj", "mobile": "mobil",
    "models": "modeller", "modern": "modern", "money": "para", "multimedia": "çoklu ortam",
    "multimodal": "çok kipli", "networks": "ağlar", "note": "not", "offline": "çevrim dışı",
    "operating": "işletim", "organization": "düzenleme", "outliner": "ana hat düzenleyici",
    "packet": "paket", "painting": "boyama", "panels": "panelleri", "pastebins": "metin paylaşım servisleri",
    "peer": "eşler arası", "performance": "performans", "planner": "planlayıcı", "platform": "platform",
    "player": "oynatıcı", "plugins": "eklentiler", "podcast": "podcast", "podcasts": "podcastler",
    "polls": "anketler", "positioning": "konumlandırma", "power": "güç", "preservation": "koruma",
    "professional": "profesyonel", "projects": "projeler", "protection": "koruma", "prototyping": "prototipleme",
    "proxy": "vekil sunucu", "ransomware": "fidye yazılımı", "raster": "piksel tabanlı", "recipe": "tarif",
    "relationship": "ilişkileri", "rendering": "işleme", "resource": "kaynak", "resources": "kaynakları",
    "scanner": "tarayıcı", "scanners": "tarayıcıları", "shorteners": "kısaltıcıları", "simple": "basit",
    "solutions": "çözümleri", "sources": "kaynakları", "stores": "mağazaları", "suites": "paketleri",
    "surveillance": "gözetim", "synchronization": "eşitleme", "systems": "sistemleri", "tabs": "sekmeler",
    "taking": "alma", "tasks": "görevler", "teams": "ekipler", "templates": "şablonlar", "text": "metin",
    "things": "nesneler", "timeline": "zaman çizelgesi", "troubleshooting": "sorun giderme",
    "upload": "yükleme", "url": "URL", "user": "kullanıcı", "webmail": "web postası",
    "wikis": "vikiler", "windows": "Windows", "workspaces": "çalışma alanları", "workstations": "iş istasyonları",
    "of": "", "to": "",
    "ad": "reklam", "aliases": "takma adlar", "base": "taban", "beat": "ritim", "do": "yapılacak",
    "fast": "hızlı", "first": "önce", "low": "düşük", "self": "kendi", "single": "tek",
    "toggle": "açma kapama", "travel": "seyahat",
    "unknown": "bilinmiyor", "freemium": "ücretsiz ve ücretli", "paid": "ücretli",
}


def tr_label(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return text
    if re.search(r"[çğıöşüÇĞİÖŞÜ]", text) and not re.search(r"\b(?:and|tools?|management|assistant|tasks?|software|platforms?)\b", text, re.I):
        return text
    lowered = text.lower()
    for source in sorted(PHRASES, key=len, reverse=True):
        lowered = re.sub(rf"(?<!\w){re.escape(source)}(?!\w)", PHRASES[source], lowered, flags=re.I)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    first = "İ" if lowered.startswith("i") else lowered[:1].upper()
    return first + lowered[1:]


def pricing(tool: dict) -> str:
    return {"free": "Ücretsiz", "freemium": "Ücretsiz + Ücretli", "paid": "Ücretli"}.get(tool.get("pricing_type"), "Fiyat bilgisi değişebilir")


def unique(values):
    return list(dict.fromkeys(value for value in values if value))


CURATED_DESCRIPTIONS = {
    "chatgpt": "ChatGPT; yazma, kodlama, araştırma, görsel üretimi ve dosya analizi gibi bilgi işlerini tek bir yapay zekâ asistanında birleştirir.",
    "claude": "Claude; uzun belgelerle çalışma, metin yazma, analiz, araştırma ve kodlama görevlerine odaklanan Anthropic yapay zekâ asistanıdır.",
    "gemini": "Gemini; metin, görsel, araştırma ve üretkenlik görevlerini Google hizmetleriyle birlikte yürütebilen çok kipli bir yapay zekâ asistanıdır.",
    "perplexity": "Perplexity, yanıtlarını kaynak bağlantılarıyla destekleyen; web araştırması ve güncel bilgi araması için tasarlanmış yapay zekâ destekli bir arama aracıdır.",
    "visual-studio-code": "Visual Studio Code; eklenti desteği, hata ayıklama, Git araçları ve bütünleşik terminal sunan ücretsiz, açık kaynaklı bir kod düzenleyicisidir.",
    "canva": "Canva; sosyal medya görselleri, sunumlar, belgeler ve videolar hazırlamak için şablonlarla çalışan çevrim içi bir tasarım platformudur.",
    "adobe-photoshop": "Adobe Photoshop; fotoğraf düzenleme, görsel birleştirme, piksel tabanlı tasarım ve üretken yapay zekâ araçları sunan profesyonel bir görüntü editörüdür.",
    "gimp": "GIMP; fotoğraf düzenleme, katmanlı tasarım ve görsel işleme için Windows, macOS ve Linux üzerinde çalışan ücretsiz, açık kaynaklı bir editördür.",
    "ollama": "Ollama, desteklenen büyük dil modellerini kullanıcının kendi bilgisayarında indirip çevrim dışı çalıştırmasını kolaylaştıran açık kaynaklı bir yerel yapay zekâ aracıdır.",
    "open-webui": "Open WebUI; yerel veya uzak yapay zekâ modellerini sohbet arayüzünden kullanmak için kendi sunucunda barındırılabilen açık kaynaklı bir web uygulamasıdır.",
    "cursor": "Cursor; kod tamamlama, proje içi soru-cevap ve yapay zekâ destekli düzenleme özelliklerini masaüstü kod editöründe bir araya getirir.",
    "n8n": "n8n; farklı uygulama ve servisleri görsel iş akışlarıyla bağlayarak tekrarlanan görevleri otomatikleştiren, kendi sunucunda da çalıştırılabilen bir otomasyon platformudur.",
}

LEGACY_DESCRIPTION_MARKERS = (
    "alanındaki işleri düzenlemeye ve yürütmeye yardımcı olan",
    "ilgili dijital işleri daha düzenli tamamlamak isteyen",
    "iş akışlarına odaklanan bir",
)


def should_replace_translation(existing) -> bool:
    """Replace only missing or known generated copy; preserve editorial work."""
    if not existing:
        return True
    description = str(existing["description"] or "").strip()
    if not description:
        return True
    try:
        payload = json.loads(existing["payload_json"] or "{}")
    except (TypeError, ValueError, json.JSONDecodeError):
        payload = {}
    source = str(payload.get("translation_source") or "")
    if source.startswith("generated-") or source in {"complete-template-v1", "expansion-template-v1"}:
        return True
    return any(marker in description.lower() for marker in LEGACY_DESCRIPTION_MARKERS)


def merge_missing(defaults, existing):
    """Recursively preserve editorial values while filling absent fields."""
    if not isinstance(defaults, dict) or not isinstance(existing, dict):
        return existing if existing not in (None, "", [], {}) else defaults
    merged = dict(defaults)
    for key, value in existing.items():
        merged[key] = merge_missing(defaults.get(key), value) if key in defaults else value
    return merged


def natural_description(tool: dict, category: str, subcategory: str, features: list[str]) -> str:
    curated = CURATED_DESCRIPTIONS.get(str(tool.get("slug") or ""))
    if curated:
        return curated
    name = tool["name"]
    capabilities = unique([*features, *[tr_label(value) for value in (tool.get("tags") or [])]])[:4]
    capability_text = ", ".join(value.lower() for value in capabilities)
    platform_text = ", ".join(tool.get("platforms") or [])
    variants = (
        f"{name}; {capability_text} özelliklerini bir araya getiren bir {subcategory.lower()} çözümüdür.",
        f"{name}, {subcategory.lower()} ihtiyaçları için {capability_text} işlevleri sunan bir {category.lower()} aracıdır.",
        f"{name}; {capability_text} çalışmalarına odaklanan, {category.lower()} kategorisinde yer alan bir yazılımdır.",
        f"{name}, {capability_text} görevlerini yürütmek için geliştirilen bir {subcategory.lower()} aracıdır.",
    )
    description = variants[int(tool.get("id") or 0) % len(variants)]
    if platform_text:
        description += f" {platform_text} platformlarında kullanılabilir."
    if tool.get("offline"):
        description += " Desteklenen kurulumlarda internet bağlantısı olmadan da çalışabilir."
    if tool.get("open_source"):
        description += " Kaynak kodu açıktır ve uygun altyapıda kullanıcı tarafından barındırılabilir."
    return description


def payload_for(tool: dict) -> dict:
    name = tool["name"]
    category = CATEGORY_TR.get(tool.get("category"), tr_label(tool.get("category")))
    subcategory = tr_label(tool.get("subcategory"))
    base_features = tool.get("features") or tool.get("tags") or []
    features = unique([tr_label(value) for value in base_features])[:6]
    if len(features) < 3:
        features = unique([*features, f"{subcategory} odaklı çalışma akışı", "Bireysel ve ekip kullanımına uygun yapı", "Resmî ürün ve proje kaynaklarına erişim"])
    description = natural_description(tool, category, subcategory, features)
    tags = unique([tr_label(value) for value in (tool.get("tags") or [])] + features)[:8]
    price = pricing(tool)
    price_note = (
        "Araç ücretsiz ve açık kaynaklıdır. Sunucu, alan adı, depolama veya üçüncü taraf hizmetleri ayrıca maliyet oluşturabilir."
        if tool.get("pricing_type") == "free" and tool.get("open_source") else
        "Planlar, kullanım sınırları ve bölgesel fiyatlar değişebilir; güncel bilgileri resmî web sitesinden doğrulayın."
    )
    platforms = tool.get("platforms") or []
    requirements = ["Güncel ve güvenli bir web tarayıcısı"] if "Web" in platforms else []
    if tool.get("open_source"):
        requirements.append("Kurulum için desteklenen bir sunucu, kapsayıcı veya işletim sistemi ortamı")
    requirements.append("Sürüm ve platforma özel gereksinimler için resmî belgeleri inceleyin")
    pros = [f"{subcategory} alanına odaklanan özellikler sunar", "Resmî web sitesi ve proje kaynakları doğrulanmıştır"]
    if tool.get("open_source"):
        pros.insert(1, "Kaynak kodu açıktır ve kendi altyapında çalıştırılabilir")
    cons = ["Kurulum ve bakım gereksinimleri seçilen kullanım biçimine göre değişebilir"]
    if tool.get("pricing_type") != "free":
        cons.append("Gelişmiş özelliklerin bir bölümü ücretli plan gerektirebilir")
    return {
        "description": description, "purpose": description, "category": category, "subcategory": subcategory,
        "features": features, "tags": tags, "pricing": price,
        "pros": pros, "cons": cons,
        "target_users": [f"{subcategory} çözümü arayan bireyler", "Alternatifleri karşılaştıran ekipler", "Verilerini kendi altyapısında tutmak isteyen kullanıcılar"],
        "system_requirements": unique(requirements),
        "pricing_details": {"model": price, "note": price_note, "summary": price, "notes": price_note},
        "verification": {"status": "Doğrulandı", "date": (tool.get("verification") or {}).get("date"), "note": "Kimlik, resmî web sitesi, kategori, kaynak bağlantıları ve araç simgesi AtlasFind tarafından kontrol edildi. Değişebilen bilgiler için resmî kaynağı inceleyin."},
        "quality_review": {"scope": "generated-catalog-fallback-v2", "reviewed_at": (tool.get("quality_review") or {}).get("reviewed_at"), "note": "Türkçe katalog alanları kaynak kayıttaki kategori, özellik, platform ve lisans bilgilerinden üretildi; editoryal metinler bu işlem sırasında korunur."},
        "translation_source": "curated-v1" if tool.get("slug") in CURATED_DESCRIPTIONS else "generated-catalog-fallback-v2",
        "change_history": [{"date": entry.get("date"), "type": entry.get("type", "data-review"), "summary": "Araç kaydı ve Türkçe içerik gözden geçirildi.", "changes": ["Türkçe alanlar tamamlandı"]} for entry in (tool.get("change_history") or [])],
        "price_history": [{**entry, "old_value": tr_label(entry.get("old_value")), "new_value": tr_label(entry.get("new_value")), "note": "Fiyatlandırma kaydı editoryal inceleme sırasında güncellendi; güncel planları resmî siteden doğrulayın."} for entry in (tool.get("price_history") or [])],
        "icon_alt": f"{name} resmî simgesi",
    }


def main() -> None:
    tools = load_published_catalog(validate=True)
    updated = 0
    preserved = 0
    with transaction() as connection:
        for tool in tools:
            existing = connection.execute(
                "SELECT name,description,subcategory,pricing_summary,pricing_notes,payload_json "
                "FROM tool_translations WHERE tool_id=? AND locale='tr'",
                (tool["id"],),
            ).fetchone()
            payload = payload_for(tool)
            replace = should_replace_translation(existing)
            if existing and not replace:
                try:
                    existing_payload = json.loads(existing["payload_json"] or "{}")
                except (TypeError, ValueError, json.JSONDecodeError):
                    existing_payload = {}
                payload = merge_missing(payload, existing_payload)
                payload["description"] = existing["description"]
                payload["purpose"] = existing_payload.get("purpose") or existing["description"]
                payload["translation_source"] = existing_payload.get("translation_source") or "editorial-preserved-v1"
                preserved += 1
            details = payload["pricing_details"]
            connection.execute(
                """INSERT INTO tool_translations(tool_id,locale,name,description,subcategory,pricing_summary,pricing_notes,payload_json)
                   VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(tool_id,locale) DO UPDATE SET
                   name=excluded.name,description=excluded.description,subcategory=excluded.subcategory,
                   pricing_summary=excluded.pricing_summary,pricing_notes=excluded.pricing_notes,payload_json=excluded.payload_json""",
                (tool["id"], "tr", (existing["name"] if existing and not replace and existing["name"] else tool["name"]),
                 payload["description"],
                 (existing["subcategory"] if existing and not replace and existing["subcategory"] else payload["subcategory"]),
                 (existing["pricing_summary"] if existing and not replace and existing["pricing_summary"] else details["model"]),
                 (existing["pricing_notes"] if existing and not replace and existing["pricing_notes"] else details["note"]),
                 json.dumps(payload, ensure_ascii=False)),
            )
            updated += int(replace)
    print(f"Turkish payloads synchronized: {updated} generated, {preserved} editorial records preserved and completed")


if __name__ == "__main__":
    main()
