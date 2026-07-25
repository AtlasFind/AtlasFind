## [0.4.1] - 2026-07-25

### Added
- Tool freshness metadata with last check, last update and next review dates.
- Scalable change history and pricing history records for every current and future tool.
- Freshness badges, stale-data warnings and listing timelines on tool and guide pages.
- Reusable editorial update checklist and dedicated freshness validation script.

### Changed
- Application version updated to v0.4.1.
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
