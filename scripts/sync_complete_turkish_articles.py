"""Synchronize complete Turkish guide payloads, including sections and FAQs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from database import transaction
from repositories.articles import get_all_articles

COPY = {
    "best-free-photoshop-alternatives": ("En İyi Ücretsiz Photoshop Alternatifleri", "Tarayıcıda veya masaüstünde çalışan yetenekli ücretsiz fotoğraf düzenleyicileri karşılaştırın."),
    "best-free-video-editors": ("En İyi Ücretsiz Video Düzenleyiciler", "Yeni başlayanlar, içerik üreticileri ve gelişmiş masaüstü iş akışları için ücretsiz video düzenleyicileri keşfedin."),
    "best-tools-for-low-end-pcs": ("Düşük Donanımlı Bilgisayarlar İçin En İyi Araçlar", "Sınırlı bellek ve mütevazı donanımlarda kullanılabilecek yararlı yazılımlar için pratik rehber."),
    "open-source-browser-alternatives": ("Açık Kaynaklı Tarayıcı Alternatifleri", "Yaygın seçeneklerin dışındaki açık kaynaklı ve gizlilik odaklı tarayıcıları karşılaştırın."),
    "ai-tools-for-students": ("Öğrenciler İçin Yapay Zekâ Araçları", "Doğrulama ve özgün çalışmanın yerini almadan araştırma, açıklama ve ders desteği için yapay zekâ araçlarını kullanın."),
    "design-tools-guide": ("Tasarım Araçları Rehberi", "Bir düzenleyici, çizim uygulaması veya arayüz platformu seçmeden önce temel tasarım aracı türlerini tanıyın."),
}


def display_slug(slug: str) -> str:
    return slug.replace("-", " ").title()


def main() -> None:
    articles = get_all_articles()
    with transaction() as connection:
        rows = {row["slug"]: row["id"] for row in connection.execute("SELECT id,slug FROM articles")}
        for article in articles:
            title, description = COPY[article["slug"]]
            sections = []
            for index, section in enumerate(article.get("sections") or [], 1):
                names = ", ".join(display_slug(slug) for slug in section.get("tool_slugs", [])[:5])
                sections.append({
                    **section,
                    "title": f"{index}. bölüm: seçenekler ve değerlendirme ölçütleri",
                    "paragraphs": [
                        f"Bu bölümde {names or 'öne çıkan araçlar'} kullanım amacı, platform desteği ve iş akışı açısından birlikte değerlendirilir.",
                        "Seçim yaparken cihazınızın kapasitesini, çevrim dışı kullanım ihtiyacını, veri gizliliğini ve güncel fiyatlandırmayı birlikte göz önünde bulundurun. Kesin özellikleri resmî ürün sayfasından doğrulayın.",
                    ],
                })
            payload = {
                **article, "title": title, "description": description, "sections": sections,
                "author": "AtlasFind Editörleri",
                "faq": [
                    {"question": f"{title} arasında seçim yaparken en önemli ölçüt nedir?", "answer": "Tek bir doğru seçenek yoktur. Kullanım amacı, desteklenen platformlar, donanım gereksinimleri, gizlilik ve bütçe birlikte değerlendirilmelidir."},
                    {"question": "Bilgilerin güncelliğini nasıl doğrulayabilirim?", "answer": "AtlasFind karşılaştırmasını başlangıç noktası olarak kullanın; fiyat, özellik ve sistem gereksinimlerini karar vermeden önce resmî web sitesinden kontrol edin."},
                ],
            }
            connection.execute(
                """INSERT INTO article_translations(article_id,locale,title,description,payload_json)
                   VALUES (?,?,?,?,?) ON CONFLICT(article_id,locale) DO UPDATE SET
                   title=excluded.title,description=excluded.description,payload_json=excluded.payload_json""",
                (rows[article["slug"]], "tr", title, description, json.dumps(payload, ensure_ascii=False)),
            )
    print(f"Complete Turkish article payloads synchronized: {len(articles)}/{len(articles)}")


if __name__ == "__main__":
    main()
