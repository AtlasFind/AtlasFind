from __future__ import annotations

from difflib import SequenceMatcher, get_close_matches
import re
import unicodedata
from time import perf_counter
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
    "alternative": {"alternative", "alternatif", "alternatifi", "yerine"},
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
    "alternative": SYNONYM_GROUPS["alternative"],
}

STOP_WORDS = {
    "bir", "ve", "veya", "ile", "için", "icin", "en", "iyi", "olan", "gibi", "aracı", "araci",
    "tool", "tools", "software", "uygulama", "program", "alternatifi", "alternative", "alternatif", "no",
}

_VOCABULARY_CACHE: dict[tuple, set[str]] = {}

FIELD_LABELS = {
    "name": "tool name",
    "tags": "tags",
    "subcategory": "subcategory",
    "category": "category",
    "target_users": "target audience",
    "description": "description",
}


def normalize_text(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold().replace("ı", "i")
    text = "".join(char for char in unicodedata.normalize("NFKD", text) if not unicodedata.combining(char))
    text = re.sub(r"[^a-z0-9+.#\s-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(value: object) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        value = " ".join(str(item) for item in value)
    return [token for token in normalize_text(value).split() if len(token) > 1 and token not in STOP_WORDS]


def contains_phrase(query: str, phrase: str) -> bool:
    normalized_phrase = normalize_text(phrase)
    if not normalized_phrase:
        return False
    return re.search(r"(?:^|\s)" + re.escape(normalized_phrase) + r"(?:$|\s)", query) is not None


def detect_search_needs(search_query: str) -> list[str]:
    query = normalize_text(search_query)
    return [name for name, phrases in INTENT_KEYWORDS.items() if any(contains_phrase(query, phrase) for phrase in phrases)]


def _catalog_signature(tools: Iterable[dict]) -> tuple:
    return tuple((str(tool.get("id", "")), str(tool.get("slug", "")), str(tool.get("name", ""))) for tool in tools)


def build_vocabulary(tools: Iterable[dict]) -> set[str]:
    tool_list = list(tools)
    signature = _catalog_signature(tool_list)
    cached = _VOCABULARY_CACHE.get(signature)
    if cached is not None:
        return cached
    vocabulary: set[str] = set()
    for tool in tool_list:
        for value in [tool.get("name"), tool.get("category"), tool.get("subcategory")]:
            vocabulary.update(tokenize(value))
        for field in ("tags", "target_users", "platforms"):
            vocabulary.update(tokenize(tool.get(field, [])))
    for phrases in SYNONYM_GROUPS.values():
        for phrase in phrases:
            vocabulary.update(tokenize(phrase))
    if len(_VOCABULARY_CACHE) >= 4:
        _VOCABULARY_CACHE.clear()
    _VOCABULARY_CACHE[signature] = vocabulary
    return vocabulary


def correct_query(search_query: str, tools: Iterable[dict]) -> str:
    original_tokens = tokenize(search_query)
    if not original_tokens:
        return normalize_text(search_query)
    vocabulary = build_vocabulary(tools)
    corrected: list[str] = []
    changed = False
    for token in original_tokens:
        if token in vocabulary or len(token) < 4:
            corrected.append(token)
            continue
        match = get_close_matches(token, vocabulary, n=1, cutoff=0.79)
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


def _intent_score(tool: dict, needs: list[str]) -> tuple[int, list[str], int]:
    score = 0
    reasons: list[str] = []
    penalties = 0
    category = _field_text(tool, "category")
    tags = _field_text(tool, "tags")
    pricing = normalize_text(tool.get("pricing_type") or tool.get("pricing"))
    languages = {normalize_text(value) for value in tool.get("languages", []) or []}

    if "free" in needs:
        if pricing == "free": score += 45; reasons.append("Free pricing matches the query")
        elif pricing == "freemium": score += 20; reasons.append("A free tier is available")
        else: penalties += 24
    if "open_source" in needs:
        if tool.get("open_source"): score += 52; reasons.append("Open-source availability matches the query")
        else: penalties += 18
    if "offline" in needs:
        if tool.get("offline"): score += 46; reasons.append("Offline use matches the query")
        else: penalties += 20
    if "privacy" in needs:
        privacy_hits = int(bool(tool.get("offline"))) + int(bool(tool.get("open_source"))) + int("privacy" in tags)
        score += privacy_hits * 15
        if privacy_hits: reasons.append("Privacy-friendly traits match the query")
    if "lightweight" in needs:
        level = normalize_text(tool.get("system_level", "unknown"))
        ram = tool.get("minimum_ram_gb")
        if level == "light": score += 42; reasons.append("Its light system profile suits older hardware")
        elif level == "medium": score += 12
        else: penalties += 16
        if isinstance(ram, (int, float)) and not isinstance(ram, bool) and ram <= 4:
            score += 20
    if "ai" in needs:
        if tool.get("ai_powered"): score += 32; reasons.append("AI features match the query")
        else: penalties += 10
    if "turkish" in needs:
        if "tr" in languages or "turkish" in languages: score += 38; reasons.append("Turkish language support matches the query")
        else: penalties += 12
    if "photo_editing" in needs:
        photo_match = any(term in tags for term in ("photo", "image", "raster", "painting")) or any(term in _field_text(tool, "subcategory") for term in ("photo", "image", "raster"))
        if category == "design" and photo_match: score += 52
        elif category == "design": score += 10
        if photo_match: score += 34; reasons.append("Photo-editing focus matches the query")
        else: penalties += 32
    if "video_editing" in needs:
        if category == "video": score += 52; reasons.append("Video-editing focus matches the query")
        elif "video" in tags: score += 28
        else: penalties += 30
    if "code_editor" in needs:
        if category == "development": score += 46
        if any(term in tags for term in ("code", "ide", "editor", "developer")): score += 34
        if category == "development" or any(term in tags for term in ("code", "ide", "editor")):
            reasons.append("Development features match the query")
        else: penalties += 28
    if "browser" in needs:
        if category == "browser": score += 70; reasons.append("Browser category matches the query")
        else: penalties += 120
    if "local_ai" in needs:
        if tool.get("offline"): score += 48
        else: penalties += 18
        if "local" in tags or "local ai" in tags: score += 38
        if tool.get("offline") or "local" in tags: reasons.append("Local/offline AI capabilities match the query")
    if "alternative" in needs:
        tool_name = _field_text(tool, "name")
        if tool_name and tool_name in normalize_text(" ".join(tokenize(tool_name))):
            pass

    return score, reasons, penalties


def score_tool(tool: dict, search_query: str, detected_needs: list[str] | None = None) -> dict:
    query = normalize_text(search_query)
    if not query:
        return {"score": 0, "reasons": [], "coverage": 0}
    needs = detected_needs or detect_search_needs(query)
    query_tokens = set(tokenize(query))
    expanded_tokens = expand_tokens(query)

    fields = {
        "name": _field_text(tool, "name"),
        "slug": _field_text(tool, "slug").replace("-", " "),
        "tags": _field_text(tool, "tags"),
        "subcategory": _field_text(tool, "subcategory"),
        "category": _field_text(tool, "category"),
        "target_users": _field_text(tool, "target_users"),
        "description": _field_text(tool, "description"),
        "pros": _field_text(tool, "pros"),
        "platforms": _field_text(tool, "platforms"),
    }
    score = 0
    reasons: list[str] = []
    name = fields["name"]
    slug = fields["slug"]

    if query == name or query == slug:
        score += 260; reasons.append("Exact tool-name match")
    elif name.startswith(query) or slug.startswith(query):
        score += 175; reasons.append("Tool name starts with the query")
    elif query in name or query in slug or name in query:
        score += 120; reasons.append("Tool name closely matches the query")

    weights = {"name": 40, "slug": 35, "tags": 28, "subcategory": 23, "category": 20, "target_users": 13, "pros": 8, "description": 6, "platforms": 5}
    matched_original: set[str] = set()
    field_hits: dict[str, set[str]] = {}
    for token in expanded_tokens:
        for field, field_text in fields.items():
            if token in field_text:
                score += weights[field]
                field_hits.setdefault(field, set()).add(token)
                if token in query_tokens:
                    matched_original.add(token)
        if len(token) >= 4:
            similarity = max((SequenceMatcher(None, token, candidate).ratio() for candidate in tokenize(name)), default=0)
            if similarity >= 0.88:
                score += round(18 * similarity)

    for field in ("name", "tags", "subcategory", "category", "target_users", "description"):
        hits = field_hits.get(field, set())
        if hits and field != "name":
            reasons.append(f"Matched {FIELD_LABELS[field]}: " + ", ".join(sorted(hits)[:3]))

    intent_score, intent_reasons, penalties = _intent_score(tool, needs)
    score += intent_score - penalties
    reasons.extend(intent_reasons)
    if "alternative" in needs:
        referenced_name = any(token in query_tokens for token in tokenize(name) if len(token) >= 4)
        if referenced_name:
            score -= 190
            reasons = [reason for reason in reasons if "Tool name" not in reason]

    coverage = len(matched_original) / max(1, len(query_tokens))
    if len(query_tokens) >= 2:
        if coverage >= 0.75: score += 32
        elif coverage >= 0.5: score += 12
        elif not needs: score -= 28
    semantic_hits = bool(field_hits) or bool(intent_reasons)
    if not semantic_hits and not reasons:
        score = 0
    if score < 18 and query != name and query != slug:
        score = 0

    unique_reasons = []
    for reason in reasons:
        if reason not in unique_reasons:
            unique_reasons.append(reason)
    return {"score": max(0, score), "reasons": unique_reasons[:3], "coverage": coverage}


def calculate_search_score(tool: dict, search_query: str, detected_needs: list[str] | None = None) -> int:
    return score_tool(tool, search_query, detected_needs)["score"]



def _candidate_tools(tools: list[dict], search_query: str, needs: list[str]) -> list[dict]:
    """Cheaply reduce large catalogs before applying the detailed scoring model."""
    if len(tools) < 750:
        return tools
    tokens = expand_tokens(search_query)
    if not tokens and not needs:
        return tools
    candidates = []
    for tool in tools:
        blob = normalize_text(" ".join([
            str(tool.get("name", "")),
            str(tool.get("slug", "")),
            str(tool.get("category", "")),
            str(tool.get("subcategory", "")),
            " ".join(map(str, tool.get("tags", []))),
            " ".join(map(str, tool.get("platforms", []))),
            " ".join(map(str, tool.get("target_users", []))),
        ]))
        if any(token in blob for token in tokens):
            candidates.append(tool)
            continue
        if "free" in needs and tool.get("pricing_type") == "free":
            candidates.append(tool)
        elif "open_source" in needs and tool.get("open_source"):
            candidates.append(tool)
        elif "offline" in needs and tool.get("offline"):
            candidates.append(tool)
        elif "ai" in needs and tool.get("ai_powered"):
            candidates.append(tool)
    return candidates or tools

def rank_tools(tools: list[dict], search_query: str) -> tuple[list[dict], dict]:
    started = perf_counter()
    corrected_query = correct_query(search_query, tools)
    needs = detect_search_needs(corrected_query)
    source_count = len(tools)
    tools = _candidate_tools(tools, corrected_query, needs)
    ranked = []
    seen: set[str] = set()
    for tool in tools:
        identity = str(tool.get("slug") or tool.get("id") or normalize_text(tool.get("name")))
        if identity in seen:
            continue
        seen.add(identity)
        result = score_tool(tool, corrected_query, needs)
        if result["score"] > 0:
            ranked.append({"tool": tool, "score": result["score"], "match": 0, "reasons": result["reasons"]})
    ranked.sort(key=lambda item: (item["score"], float(item["tool"].get("rating", 0) or 0), int(item["tool"].get("popularity_score", 0) or 0), normalize_text(item["tool"].get("name", ""))), reverse=True)
    highest = ranked[0]["score"] if ranked else 0
    for item in ranked:
        item["match"] = max(1, min(100, round((item["score"] / highest) * 100))) if highest else 0
    duration_ms = round((perf_counter() - started) * 1000, 2)
    return ranked, {
        "detected_needs": needs,
        "corrected_query": corrected_query,
        "did_correct": corrected_query != normalize_text(search_query),
        "duration_ms": duration_ms,
        "result_count": len(ranked),
        "candidate_count": len(tools),
        "source_count": source_count,
    }


def search_suggestions(tools: list[dict], query: str, limit: int = 8) -> list[dict]:
    normalized = normalize_text(query)
    if len(normalized) < 2:
        return []
    suggestions = []
    for tool in tools:
        name = normalize_text(tool.get("name"))
        score = 100 if name.startswith(normalized) else 70 if normalized in name else round(SequenceMatcher(None, normalized, name).ratio() * 45)
        if score >= 28:
            suggestions.append({"label": tool.get("name", ""), "value": tool.get("name", ""), "type": "tool", "score": score})
    intent_labels = ["Free photo editor", "Offline AI assistant", "Open source browser", "Lightweight code editor", "Free video editor", "Turkish supported AI"]
    for label in intent_labels:
        label_norm = normalize_text(label)
        if normalized in label_norm or SequenceMatcher(None, normalized, label_norm).ratio() >= 0.45:
            suggestions.append({"label": label, "value": label, "type": "query", "score": 55})
    suggestions.sort(key=lambda item: (item["score"], item["label"]), reverse=True)
    seen, output = set(), []
    for item in suggestions:
        key = item["value"].casefold()
        if key in seen: continue
        seen.add(key)
        output.append({k: v for k, v in item.items() if k != "score"})
        if len(output) >= limit: break
    return output


def alternative_queries(search_query: str, corrected_query: str, needs: list[str]) -> list[str]:
    alternatives = []
    if corrected_query and corrected_query != normalize_text(search_query): alternatives.append(corrected_query)
    labels = {"photo_editing": "free photo editor", "video_editing": "free video editor", "code_editor": "lightweight code editor", "browser": "privacy focused browser", "local_ai": "offline local AI", "ai": "AI tools"}
    for need in needs:
        if need in labels and labels[need] not in alternatives: alternatives.append(labels[need])
    return alternatives[:4]
