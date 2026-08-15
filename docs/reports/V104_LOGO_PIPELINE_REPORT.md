# AtlasFind v1.0.4 Logo Pipeline

## Durum

- Katalogdaki araç: 600
- Oluşturulan logo kuyruğu: 600
- Otomatik yayınlanan aday: 0
- Manuel onay zorunluluğu: etkin

## Akış

1. `build_logo_queue_v104.py` doğrulanmamış araçları kuyruğa alır.
2. `discover_tool_logos_v104.py` yalnızca kayıtlı resmî HTTPS sitesini tarar.
3. Web manifest, icon, apple-touch-icon ve Open Graph adayları puanlanır.
4. Adaylar otomatik yayımlanmaz.
5. `review_logo_candidate_v104.py` ile bir aday onaylanır.
6. `import_tool_logos_v104.py` onaylanan dosyayı indirir, doğrular, optimize eder ve yerel saklar.
7. Branding metadata, SHA-256 checksum ve kaynak kaydı katalogda tutulur.

## Güvenlik

- HTTP, localhost, özel IP, file ve javascript adresleri engellenir.
- Yönlendirme sayısı ve indirme boyutu sınırlıdır.
- MIME türü, piksel alanı ve gerçek görsel açılabilirliği doğrulanır.
- SVG script, event handler ve haricî kaynak kontrollerinden geçer.
- Aday editör onayı olmadan yayınlanamaz.
