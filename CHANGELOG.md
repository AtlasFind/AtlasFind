# Changelog

## 1.9.2 - 2026-08-11

- Changed email verification to a two-step GET-and-confirm flow so mail security scanners cannot consume one-time links before users open them.

## 1.9.1 - 2026-08-11

- Added Resend HTTPS API delivery for verification and password-reset emails on Render Free.
- Kept SMTP as a fallback for hosting plans that permit outbound mail ports.
- Added safe API failure logging and transactional email tests.

## 1.9.0 - 2026-08-08

- Completed the persistent user registration, email verification and secure login flow.
- Added one-hour, single-use password reset links with account-enumeration protection.
- Added Turkish and English forgot/reset password screens and transactional emails.
- Added production Gmail SMTP environment wiring without storing secrets in source control.

## 1.8.3 - 2026-08-08

- Moved every header navigation link into the single three-dot menu.
- Reduced the default header to brand, account, language, theme and menu controls.
- Moved Useful Collections below the main tools and category discovery sections.

## 1.8.2 - 2026-08-08

- Restored the single three-dot utility menu on desktop and mobile.
- Moved About, Collaboration, Ratings, Contact and legal pages back into that menu.
- Added outside-click and Escape closing behavior without horizontal overflow.

## 1.8.1 - 2026-08-08

- Restored the familiar ChatGPT, Claude, Gemini and Perplexity homepage order.
- Collapsed advanced homepage filters behind a compact filter button.
- Polished score badges, card spacing and localized pricing labels.
- Verified the refreshed layout at desktop and mobile breakpoints.

## 1.8.0 - 2026-08-08

- Added a deterministic AtlasFind catalog score to all 1,000 public tools.
- Kept automated catalog, human-reviewed editor and community scores separate.
- Added score breakdowns to tool details and scores to cards, sorting, filters and comparisons.
- Added Turkish and English methodology disclosures plus automated coverage tests.

## v1.0.3 - Transparent Rating System

- Replaced unverified legacy scores with a versioned, evidence-linked 10-point rating model.
- Added category-specific weight profiles, minimum coverage and independent approval rules.
- Added rating confidence, methodology, source, external rating and user rating structures.
- Added rating administration, change-log and user-review database tables.
- Added Turkish and English rating methodology pages and detailed tool-page rating UI.
- Added migration, validation, recalculation, benchmark and unit-test scripts.
- Backed up and hid all 600 legacy seed scores instead of presenting them as verified ratings.

## [1.0.1-hotfix] - 2026-07-28

- Navbar dil seçicisi tüm ekran genişliklerinde görünür hâle getirildi.
- Dil kodları açık biçimde `EN / TR` olarak gösteriliyor.
- Ana sayfa dil istatistiği `EN / TR` olarak güncellendi.
- Ana sayfadaki sabit `Categories` metni çeviri sistemine bağlandı.
- Kırık Simple Icons CDN istekleri yerel ikon dosyalarına yönlendirildi.


## v1.0.1 - Turkish localization completion

- Expanded the centralized EN/TR translation catalogs.
- Localized remaining public templates, accessibility labels, JavaScript interface messages and admin screens.
- Changed the compact language selector to EN / TR and highlighted the active locale.
- Added safe locale fallback validation and a localization audit script.
# Changelog

## v1.0.0 - First Stable Release

- Promoted the application version to `1.0.0`.
- Corrected production SEO and Render configuration to use `https://atlasfind.org`.
- Added trusted proxy handling and an optional production Host-header allow-list.
- Replaced unsafe inline-script CSP permission with per-request script nonces.
- Added request IDs to responses and strengthened browser security headers.
- Added rate limiting for public API endpoints and explicit TRACE/TRACK rejection.
- Added a localized 405 error page and bounded public search query length.
- Strengthened `/ready` with SQLite integrity, tool, translation and category checks.
- Added safe SQLite backups before production migrations and disabled destructive automatic reseeding of non-empty databases.
- Hardened Gunicorn lifecycle settings with graceful timeout and request recycling.
- Added a full v1.0.0 release validator, deployment checklist and security policy.
- Updated README, deployment documentation, CHANGELOG and ROADMAP.

## v0.9.9-dev - Public Beta Final Check

- Added a consolidated public-beta validator covering required files, routes, error handlers, translations, static assets, database counts and known regressions.
- Added optional real Flask route tests that run automatically when dependencies are installed.
- Localized 400, 413, 429 and 500 error pages and the 404 search placeholder.
- Localized guide, recommendation, collection and 404 breadcrumbs.
- Added tools, legal and contact pages to the multilingual sitemap source list.
- Kept runtime route approval pending until local Flask and browser tests are completed.

## v0.9.8-dev - Comparison and Recommendation System

- Rebuilt the localized two-to-four tool comparison flow.
- Prevented duplicate selections both in JavaScript and on the server.
- Safely ignores unavailable comparison slugs instead of crashing the page.
- Localized comparison rows, actions, empty states, preference controls and SEO.
- Updated recommendation category matching for the v0.9.4 taxonomy.
- Improved mobile horizontal comparison behavior and long-content handling.
- Added `scripts/validate_compare_recommendations_v098.py`.
- Relaxed older validators so later development versions do not fail only because the version number changed.

# v0.9.7-dev - Professional tool detail pages

- Rebuilt the bilingual tool detail layout, navigation, summaries, requirements, pros/cons, verification and alternatives.
- Preserved localized URLs for tool and comparison links.
- Added responsive mobile behavior and long-content safeguards.


## v0.9.4-dev.1 - Localized category identity fix

- Fixed Turkish category directory counts showing zero while English counts were correct.
- Added canonical category resolution for old and new Turkish category labels.
- Restored Turkish category detail results without changing the 600-tool catalog.
- Extended taxonomy validation to test Turkish and English category parity.

# Changelog

## v0.9.4-dev - Category and Subcategory System

- Consolidated 26 overlapping category labels into 18 canonical categories.
- Added bilingual category names, descriptions, icons and legacy aliases in `taxonomy.py`.
- Added localized `/tr/categories` and `/en/categories` directory pages.
- Added category landing summaries and subcategory routes.
- Updated navigation, breadcrumbs, canonical paths and sitemap category entries.
- Migrated all 600 JSON and SQLite records while preserving tool count.
- Added migration and validation scripts for taxonomy integrity.

# AtlasFind Changelog

## [0.9.3-dev] - Search, Filter and Pagination

- Added catalog search to `/tr/tools` and `/en/tools`.
- Added relevance sorting, typo correction hints and Turkish character normalization support.
- Increased catalog pagination to 24 tools per page.
- Added numbered pagination with compact ellipsis windows.
- Preserved search and filter query parameters between pages.
- Added duplicate-result protection and search duration measurement.
- Improved empty-result actions in Turkish and English.
- Added `scripts/validate_search_pagination_v093.py`.

# Changelog

## [0.9.2-dev] - Professional Catalog Experience

### Added
- Professional catalog filter sidebar for category, subcategory, pricing, platform, rating and feature filters.
- Active filter chips, clear-all behavior and mobile filter drawer controls.
- Grid/list catalog view with local browser preference persistence.
- Filter-preserving previous and next page links.
- Turkish and English translations for every new catalog control.
- `scripts/validate_catalog_v092.py` for static, translation and 600-tool data checks.

### Changed
- Catalog cards now show category hierarchy, up to three platform badges and clean RAM fallback text.
- Long names and descriptions receive stronger desktop and mobile overflow protection.
- Catalog cards use one large accessible detail link without inline JavaScript handlers.

### Status
- Development package only. v0.9.2 is not marked complete until local Flask route, browser and mobile tests are approved.

# AtlasFind v0.9.1.2

- Removed fragile inline icon handlers that executed before JavaScript loaded.
- Added centralized icon initialization, fallback and monogram handling.
- Added asset cache busting and narrow-screen layout safeguards.
- Broken or tiny remote icons now fall back without console errors.

## v0.9.1 - Catalog UI and icon quality hotfix

- Added bilingual `/tools` catalog route.
- Added resilient Simple Icons → favicon → monogram icon fallback.
- Redesigned catalog cards, tool detail layout and contact email card.
- Improved responsive spacing, readability and pagination.

# Changelog

## v0.9.0 - Expanded catalog and public beta content
- Expanded the directory from 100 to 600 tools across 18 balanced categories.
- Added domain-based application icons with a local initial fallback.
- Added 500 Turkish catalog translations for the new directory entries.
- Added `atlasfindd@gmail.com` through `ATLASFIND_CONTACT_EMAIL`.
- Added catalog validation and translation synchronization scripts.
- Updated deployment bootstrap to rebuild an outdated catalog automatically.

# v0.8.1 - Public Beta Readiness

- Added bilingual privacy, terms, cookie and contact pages.
- Added an essential-storage notice and public beta validation.
- Expanded footer navigation and mobile public-page layout.

# Changelog
### v0.8.1 hotfix
- Fixed public-page breadcrumb generation when the current breadcrumb has no URL.
- Added trailing-slash support for privacy, terms, cookies and contact routes.
- Fixed the translated home label on safe error pages.
- Made localized path generation tolerate non-clickable breadcrumb items.


## v0.8.0 - Deployment and Public Beta

- Added production WSGI entry point and Gunicorn startup.
- Added Docker and Render deployment configuration.
- Added `/health` and `/ready` service checks.
- Added configurable persistent SQLite database path.
- Added safe database bootstrap and first-deploy catalog seeding.
- Added deployment validation and production documentation.
- Added domain, HTTPS, backup and release checklists.

## v0.7.1 - Security and Production Readiness

### Added
- Centralized environment-based production security configuration.
- In-memory sliding-window rate limits for administrator login attempts.
- Rotating application logs with request reference IDs.
- Safe 400, 413, 429 and 500 error pages without traceback disclosure.
- Content Security Policy, clickjacking, referrer, permissions and HSTS headers.
- `.env.example` and a security validation script.

### Changed
- Admin sessions now expire after 30 minutes of inactivity.
- Proxy forwarding headers are trusted only when explicitly enabled.
- Admin responses are marked private and `no-store`.
- Debug mode is disabled by default and forcibly disabled in production.
- Production startup rejects missing or weak application secrets.
- Application version updated to v0.7.1.

## v0.7.0 - Performance and Scalability

- Replaced per-tool translation queries with bulk translation loading.
- Added database-aware in-process caches for localized tools and articles.
- Added SQLite WAL, memory cache, busy timeout and normal synchronous settings.
- Added indexes for published tools, articles and translation lookups.
- Added long-lived static asset caching and conservative public page cache headers.
- Added a local performance benchmark script.

[v0.6.1] - 2026-07-27

### Added
- English and Turkish locale-prefixed public URLs.
- JSON translation catalogs with English fallback behavior.
- Navbar language switcher that keeps users on the equivalent page.
- Localized canonical URLs, hreflang tags and multilingual sitemap entries.
- SQLite translation tables and the 003_multilingual migration.
- Translation validation command for interface keys and database locale records.

### Changed
- Public unprefixed URLs now redirect permanently to the English locale.
- Tool and article repositories can apply locale-specific translations with safe fallback.
- Application version updated to v0.6.1.

## [v0.6.0] - 2026-07-27

### Added
- Dynamic robots.txt and sitemap.xml generated from published SQLite records.
- Open Graph and Twitter card metadata.
- WebSite, SoftwareApplication, Article, FAQPage and BreadcrumbList JSON-LD.
- Shared breadcrumb component and custom 404 page.
- Legacy URL 301 redirects for tools, categories and guides.
- Internal link and SEO validation scripts.

### Changed
- Centralized canonical URLs and SEO metadata around the configured production domain.
- Search, filtered, comparison and recommendation result pages now use safer indexing directives.
- Application version updated to v0.6.0.

# Changelog

## [v0.5.1] - 2026-07-25

### Fixed
- Prevented incomplete admin-created tool records from crashing public detail pages.

### Added
- Password-hashed administrator accounts and protected admin sessions.
- CSRF protection, login-attempt throttling and administrator audit logs.
- Dashboard, tool/article editors, draft/publish/archive workflows and previews.
- Category and tag management plus validated bulk JSON import.
- Database migration `002_admin_panel` and administrator setup/test scripts.

### Changed
- Public repositories now return only published tools and articles.
- Application version updated to v0.5.1.

### Security
- Secret key can be supplied through `ATLASFIND_SECRET_KEY`.
- Session cookies use HttpOnly and SameSite=Lax; Secure can be enabled for HTTPS.

## [v0.5.0] - 2026-07-25

### Added
- SQLite database schema and migration tracking.
- JSON-to-SQLite migration and verification scripts.
- Repository layer for tools and editorial content.
- Safe SQLite backup command.

### Changed
- The application now reads tools and articles from SQLite.
- JSON files remain available as migration and rollback sources.

## [0.4.1] - 2026-07-25

### Added
- Tool freshness metadata with last check, last update and next review dates.
- Scalable change history and pricing history records for every current and future tool.
- Freshness badges, stale-data warnings and listing timelines on tool and guide pages.
- Reusable editorial update checklist and dedicated freshness validation script.

### Changed
- Application version updated to v0.5.0.
- Tool and content schemas now validate freshness dates, statuses and history records.

### Preserved
- Existing search, recommendations, comparison, categories and editorial guide behavior.

## [0.4.0] - 2026-07-25

### Added
- Data-driven editorial content system for guides, alternatives, comparisons and category articles.
- Guides index with content-type and category filters.
- Article pages with table of contents, FAQs, related tools and related guides.
- Content validation for slugs, dates, sections, FAQs and tool/article references.
- Category-to-guide internal linking and canonical article URLs.

### Changed
- Navigation and footer now include the Guides section.
- Category pages can surface related editorial content.
- Application version updated to v0.4.0.

### Preserved
- Existing search, filters, recommendations, categories and comparison behavior.

## [0.3.1] - 2026-07-25

### Added
- Search quality dataset with expected and forbidden results.
- Recommendation quality test profiles.
- Human-readable search match explanations.

### Changed
- Tightened relevance scoring and reduced unrelated matches.
- Limited popularity to a final tie-breaker.
- Improved recommendation reasons and mismatch explanations.

### Fixed
- Prevented search-result cards from failing when explanation data is absent.
- Moved search result explanations into a compact top-right popover.

## [0.3.0] - 2026-07-25

### Added
- Typo-tolerant Turkish and English smart search
- Synonym and natural-query intent detection
- Search suggestions and alternative queries
- Automated search quality checks

### Changed
- Weighted search ranking now prioritizes exact names, tags, categories, and user intent
- Search remains compatible with all existing URL filters

# Changelog

## [0.2.2] - 2026-07-25
### Added
- Two-to-four tool comparison with shareable URL parameters
- Difference highlighting and optional common-feature hiding
- Pricing, platform, system, language, pros, cons and use-case comparison
- Preference-based best-fit result using the existing local recommendation engine
- Responsive horizontal comparison layout for mobile devices

## [0.2.1] - 2026-07-25
### Added
- Local rule-based recommendation engine with no external AI API
- Preference form for purpose, platform, budget, hardware, experience, privacy and offline use
- Match percentages with transparent recommendation and mismatch explanations
- Scalable scoring across every current and future tool entry

## [0.2.0] - 2026-07-25
### Added
- Scalable category and subcategory metadata
- Category and curated collection pages
- Popular, newest and editor-choice discovery metadata
- Sorting and pagination for discovery pages
- Dataset validation for discovery fields

# Changelog

## [v0.1.3] - Advanced Filtering and Data Infrastructure

### Added
- Server-side multi-filter engine
- Pricing, open-source, offline, AI and platform filters
- RAM, system-level and Turkish-support filters
- URL-preserved filter state and removable active-filter chips
- Dynamic result count and filter reset controls
- Expanded dataset validation for every current and future tool

### Changed
- Quick filters now use real filter parameters instead of search keywords
- Tool data schema now includes normalized pricing, RAM, system level and language fields
- Missing optional filter data is handled safely without crashing the application

## [v0.1.2] - Professional Tool Pages

### Added
- Pros and cons, pricing details, target users, system requirements and verification metadata

### Changed
- Professional tool detail page layout and alternative presentation

## [v0.1.1] - Premium Appearance

### Added
- Shared base template, responsive navigation, footer and accessible interface states

### Changed
- Premium navbar, hero, tool cards, themes and mobile layout

## [v0.1.0] - Foundation

### Added
- Flask application, search, cards, details, comparison, themes, responsive design and JSON dataset


### v0.6.1 Turkish content completion
- Added complete Turkish content records for all 100 published tools, including descriptions, categories, tags, pros, cons, target users, requirements, pricing notes, verification notes and history labels.

## [0.9.5-dev] - 2026-07-28

### Added
- Transparent per-tool data-quality status: verified, partially verified, unverified, or review due.
- Ten-tool internal consistency pilot covering ChatGPT, Visual Studio Code, Blender, DaVinci Resolve, Audacity, LibreOffice, Firefox, Bitwarden, Dropbox and Steam.
- Automated data-quality audit and JSON/Markdown reports.
- Catalog and detail-page quality labels in Turkish and English.
- JSON/SQLite consistency validation for quality metadata.

### Changed
- Pricing type values are deterministically normalized where the visible pricing model provides an exact mapping.
- APP_VERSION advanced to `0.9.5-dev`.

### Important
- No tool is automatically marked fully verified. Live pricing, platform support and feature availability still require individual editorial confirmation against official sources.

## [0.9.6-dev] - 2026-07-28

### Added
- Generated local SVG monogram fallback cache for all 600 tools.
- Shared icon metadata and deterministic initials for catalog, detail, comparison, recommendation and article cards.
- Icon audit and validation scripts with JSON and Markdown reports.
- Local SVG site favicon to prevent favicon 404 responses.

### Changed
- External Google favicon fallback URLs were replaced by local generated SVG fallbacks.
- Runtime icon validation now rejects tiny and extreme-aspect images before falling back.
- JSON and SQLite icon payloads are synchronized.
- APP_VERSION advanced to `0.9.6-dev`.

### Note
- Primary Simple Icons URLs remain in place where configured. The new local cache is the reliable fallback and reduces dependence on third-party favicon services.

## v1.0.2 - Modular catalog foundation (Phase 1)

- Added a category-based catalog source under `data/catalog/` with a deterministic manifest.
- Added a strict catalog loader with path traversal protection and JSON parsing errors.
- Added cross-file duplicate checks for IDs, slugs, names and exact website URLs.
- Added publication and verification states without falsely marking legacy records as verified.
- Added source-reference fields for future evidence-based data reviews.
- Added canonical taxonomy files, a JSON Schema document and generated lookup indexes.
- Updated database bootstrap and JSON-to-SQLite migration to read the modular catalog source.
- Added catalog build, validation and 100/1,000/5,000/10,000-record benchmark scripts.
- Added large-catalog candidate prefiltering to the existing search ranking pipeline.

### v1.0.2 Phase 2
- Added official-source taxonomy and claim-level evidence requirements.
- Added strict publication-readiness auditing and evidence freshness warnings.
- Added deterministic verification batch generation for editorial review.
- Strengthened JSON Schema and catalog validation for source references.

## v1.0.2 Final Release

- Added consolidated `validate_release_v102.py` release gate.
- Added `run_atlasfind.bat`, `test_release.bat`, and Turkish start instructions.
- Finalized modular catalog, evidence audit, compatibility build, and scale-test tooling.
- Preserved honest catalog state: 5 strict verified records and 595 pending records.

### v1.0.3 Dual Rating UI Hotfix
- Removed misleading `★ 0` displays from tool cards.
- Added a visible Rating tab to tool detail navigation.
- Added side-by-side AtlasFind and user rating cards near the top of tool details.
- Added the user voting form and transparent calculation explanations to the Rating section.


## v1.0.4 - Professional image infrastructure
- Added structured branding metadata to all 600 tool records.
- Added a local-first image resolver with checksum cache busting and safe initials fallbacks.
- Added path traversal, dangerous SVG, MIME, size, pixel-area and source URL validation.
- Added image migration, validation and optimization scripts.
- Added an admin image inventory dashboard.
- Removed runtime dependence on remote logo URLs for public rendering.

### v1.0.4 Logo Pipeline Hotfix
- Added a 600-tool official-site logo discovery queue.
- Added manifest, icon, Apple touch icon and Open Graph candidate discovery.
- Added SSRF-safe remote URL validation and limited downloads.
- Added mandatory candidate review before import.
- Added secure local WebP/SVG import, checksum, metadata and backup handling.
- Added queue reporting and automated pipeline tests.
