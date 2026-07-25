from __future__ import annotations

from difflib import SequenceMatcher, get_close_matches
import re
import unicodedata
from typing import Iterable

SYNONYM_GROUPS = {
    "free": {"free", "ücretsiz", "ucretsiz", "bedava", "no cost"},
    "photo": {"photo", "photos", "fotoğraf", "fotograf", "resim", "image", "görsel", "gorsel"},
    "video": {"video", "video editor", "video editing", "video düzenleme", "video duzenleme", "video editörü", "video editoru"},
    "code": {"code", "coding", "programming", "kod", "kodlama", "programlama", "developer", "geliştirici", "gelistirici"},
    "browser": {"browser", "tarayıcı", "tarayici", "web browser"},
    "ai": {"ai", "artificial intelligence", "yapay zeka", "yapay zekâ"},
    "offline": {"offline", "çevrimdışı", "cevrimdisi", "internetsiz", "internet olmadan"},
    "open_source": {"open source", "opensource", "açık kaynak", "acik kaynak"},
    "privacy": {"privacy", "private", "gizlilik", "mahremiyet"},
    "lightweight": {"lightweight", "hafif", "eski bilgisayar", "düşük sistem", "dusuk sistem", "low end", "az ram"},
    "turkish": {"turkish", "türkçe", "turkce", "türkçe destekli", "turkce destekli"},
    "alternative": {"alternative", "alternatif", "yerine"},
}

INTENT_KEYWORDS = {
    "free": SYNONYM_GROUPS["free"],
    "open_source": SYNONYM_GROUPS["open_source"],
    "offline": SYNONYM_GROUPS["offline"],
    "privacy": SYNONYM_GROUPS["privacy"],
    "lightweight": SYNONYM_GROUPS["lightweight"],
    "ai": SYNONYM_GROUPS["ai"],
    "turkish": SYNONYM_GROUPS["turkish"],
    "photo_editing": SYNONYM_GROUPS["photo"] | {"photoshop", "photo editing", "image editor", "raster"},
    "video_editing": SYNONYM_GROUPS["video"] | {"premiere", "davinci"},
    "code_editor": SYNONYM_GROUPS["code"] | {"code editor", "ide", "text editor", "vscode", "visual studio code"},
    "browser": SYNONYM_GROUPS["browser"] | {"chrome", "firefox"},
    "local_ai": {"local ai", "yerel ai", "yerel yapay zeka", "bilgisayarımda çalışan ai", "bilgisayarimda calisan ai"},
}

STOP_WORDS = {
    "bir", "ve", "veya", "ile", "için", "icin", "en", "iyi", "olan", "gibi", "aracı", "araci",
    "tool", "tools", "software", "uygulama", "program", "alternatifi", "alternative", "alternatif",
}


def normalize_text(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = text.replace("ı", "i")
    text = "".join(char for char in unicodedata.normalize("NFKD", text) if not unicodedata.combining(char))
    text = re.sub(r"[^a-z0-9+.#\s-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(value: object) -> list[str]:
    return [token for token in normalize_text(value).split() if len(token) > 1 and token not in STOP_WORDS]


def contains_phrase(query: str, phrase: str) -> bool:
    return normalize_text(phrase) in query


def detect_search_needs(search_query: str) -> list[str]:
    query = normalize_text(search_query)
    needs = []
    for name, phrases in INTENT_KEYWORDS.items():
        if any(contains_phrase(query, phrase) for phrase in phrases):
            needs.append(name)
    return needs


def build_vocabulary(tools: Iterable[dict]) -> set[str]:
    vocabulary: set[str] = set()
    for tool in tools:
        for value in [tool.get("name"), tool.get("category"), tool.get("subcategory")]:
            vocabulary.update(tokenize(value))
        for field in ("tags", "target_users", "platforms"):
            for value in tool.get(field, []) or []:
                vocabulary.update(tokenize(value))
    for phrases in SYNONYM_GROUPS.values():
        for phrase in phrases:
            vocabulary.update(tokenize(phrase))
    return vocabulary


def correct_query(search_query: str, tools: Iterable[dict]) -> str:
    original_tokens = tokenize(search_query)
    if not original_tokens:
        return normalize_text(search_query)
    vocabulary = build_vocabulary(tools)
    corrected = []
    changed = False
    for token in original_tokens:
        if token in vocabulary or len(token) < 4:
            corrected.append(token)
            continue
        match = get_close_matches(token, vocabulary, n=1, cutoff=0.78)
        if match:
            corrected.append(match[0])
            changed = changed or match[0] != token
        else:
            corrected.append(token)
    return " ".join(corrected) if changed else normalize_text(search_query)


def expand_tokens(search_query: str) -> set[str]:
    query = normalize_text(search_query)
    expanded = set(tokenize(query))
    for phrases in SYNONYM_GROUPS.values():
        normalized_phrases = {normalize_text(phrase) for phrase in phrases}
        if any(phrase in query for phrase in normalized_phrases):
            for phrase in normalized_phrases:
                expanded.update(tokenize(phrase))
    return expanded


def _field_text(tool: dict, field: str) -> str:
    value = tool.get(field, "")
    if isinstance(value, list):
        return normalize_text(" ".join(str(item) for item in value))
    if isinstance(value, dict):
        return normalize_text(" ".join(str(item) for item in value.values()))
    return normalize_text(value)


def calculate_search_score(tool: dict, search_query: str, detected_needs: list[str] | None = None) -> int:
    query = normalize_text(search_query)
    if not query:
        return 0
    detected_needs = detected_needs or detect_search_needs(query)
    corrected = query
    tokens = expand_tokens(corrected)

    name = _field_text(tool, "name")
    slug = _field_text(tool, "slug").replace("-", " ")
    category = _field_text(tool, "category")
    subcategory = _field_text(tool, "subcategory")
    tags = _field_text(tool, "tags")
    description = _field_text(tool, "description")
    target_users = _field_text(tool, "target_users")
    pros = _field_text(tool, "pros")
    platforms = _field_text(tool, "platforms")

    score = 0
    if query == name or query == slug:
        score += 220
    elif name.startswith(query) or slug.startswith(query):
        score += 150
    elif query in name or query in slug or name in query:
        score += 105

    field_weights = {
        name: 34,
        slug: 30,
        tags: 22,
        subcategory: 18,
        category: 16,
        target_users: 12,
        pros: 8,
        description: 6,
        platforms: 5,
    }
    for token in tokens:
        for field_text, weight in field_weights.items():
            if token in field_text:
                score += weight
        if len(token) >= 4:
            best_similarity = max((SequenceMatcher(None, token, candidate).ratio() for candidate in tokenize(name)), default=0)
            if best_similarity >= 0.86:
                score += round(24 * best_similarity)

    pricing = normalize_text(tool.get("pricing_type") or tool.get("pricing"))
    tool_tags = set(tokenize(tool.get("tags", [])))
    languages = {normalize_text(value) for value in tool.get("languages", []) or []}

    if "free" in detected_needs:
        score += 45 if pricing == "free" else 22 if pricing == "freemium" else -18
    if "open_source" in detected_needs:
        score += 48 if tool.get("open_source") else -12
    if "offline" in detected_needs:
        score += 42 if tool.get("offline") else -14
    if "privacy" in detected_needs:
        score += 20 if tool.get("offline") else 0
        score += 18 if tool.get("open_source") else 0
        score += 18 if any(tag in tool_tags for tag in {"privacy", "encryption", "local", "self", "hosted"}) else 0
    if "lightweight" in detected_needs:
        level = normalize_text(tool.get("system_level", "unknown"))
        ram = tool.get("minimum_ram_gb")
        score += 38 if level == "light" else 15 if level == "medium" else -10
        if isinstance(ram, (int, float)) and ram <= 4:
            score += 20
    if "ai" in detected_needs:
        score += 30 if tool.get("ai_powered") else -8
    if "turkish" in detected_needs:
        score += 35 if "tr" in languages or "turkish" in languages else -8
    if "photo_editing" in detected_needs:
        score += 42 if category == "design" else 0
        score += 30 if any(term in tags for term in ("photo", "image", "raster", "painting")) else 0
    if "video_editing" in detected_needs:
        score += 48 if category == "video" else 0
        score += 28 if "video" in tags else 0
    if "code_editor" in detected_needs:
        score += 42 if category == "development" else 0
        score += 30 if any(term in tags for term in ("code", "ide", "editor", "developer")) else 0
    if "browser" in detected_needs:
        score += 58 if category == "browser" else 0
    if "local_ai" in detected_needs:
        score += 45 if tool.get("offline") else -10
        score += 35 if "local" in tags or "local ai" in tags else 0

    return max(0, score)


def rank_tools(tools: list[dict], search_query: str) -> tuple[list[dict], dict]:
    corrected_query = correct_query(search_query, tools)
    needs = detect_search_needs(corrected_query)
    ranked = []
    for tool in tools:
        score = calculate_search_score(tool, corrected_query, needs)
        if score > 0:
            ranked.append({"tool": tool, "score": score, "match": 0})
    ranked.sort(
        key=lambda item: (
            item["score"],
            float(item["tool"].get("rating", 0) or 0),
            int(item["tool"].get("popularity_score", 0) or 0),
        ),
        reverse=True,
    )
    highest = ranked[0]["score"] if ranked else 0
    for item in ranked:
        item["match"] = max(1, min(100, round((item["score"] / highest) * 100))) if highest else 0
    return ranked, {
        "detected_needs": needs,
        "corrected_query": corrected_query,
        "did_correct": corrected_query != normalize_text(search_query),
    }


def search_suggestions(tools: list[dict], query: str, limit: int = 8) -> list[dict]:
    normalized = normalize_text(query)
    if len(normalized) < 2:
        return []
    suggestions = []
    for tool in tools:
        name = normalize_text(tool.get("name"))
        score = 0
        if name.startswith(normalized):
            score = 100
        elif normalized in name:
            score = 70
        else:
            score = round(SequenceMatcher(None, normalized, name).ratio() * 45)
        if score >= 28:
            suggestions.append({"label": tool.get("name", ""), "value": tool.get("name", ""), "type": "tool", "score": score})
    intent_labels = [
        "Free photo editor", "Offline AI assistant", "Open source browser",
        "Lightweight code editor", "Free video editor", "Turkish supported AI",
    ]
    for label in intent_labels:
        label_norm = normalize_text(label)
        if normalized in label_norm or SequenceMatcher(None, normalized, label_norm).ratio() >= 0.45:
            suggestions.append({"label": label, "value": label, "type": "query", "score": 55})
    suggestions.sort(key=lambda item: (item["score"], item["label"]), reverse=True)
    seen = set()
    output = []
    for item in suggestions:
        key = item["value"].casefold()
        if key in seen:
            continue
        seen.add(key)
        output.append({k: v for k, v in item.items() if k != "score"})
        if len(output) >= limit:
            break
    return output


def alternative_queries(search_query: str, corrected_query: str, needs: list[str]) -> list[str]:
    alternatives = []
    if corrected_query and corrected_query != normalize_text(search_query):
        alternatives.append(corrected_query)
    labels = {
        "photo_editing": "free photo editor",
        "video_editing": "free video editor",
        "code_editor": "lightweight code editor",
        "browser": "privacy focused browser",
        "local_ai": "offline local AI",
        "ai": "AI tools",
    }
    for need in needs:
        if need in labels and labels[need] not in alternatives:
            alternatives.append(labels[need])
    return alternatives[:4]
