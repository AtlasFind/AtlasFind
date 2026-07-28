from __future__ import annotations


def normalize_text(value):
    return str(value or "").strip().casefold()


def normalize_platform(value):
    value = normalize_text(value)
    aliases = {"mac": "macos", "osx": "macos", "web app": "web"}
    return aliases.get(value, value)


RECOMMENDATION_PURPOSES = {
    "writing": {"label": "Writing and research", "categories": {"artificial intelligence", "productivity", "office and documents"}, "keywords": {"writing", "research", "notes", "assistant", "documents"}},
    "coding": {"label": "Coding and software development", "categories": {"development", "artificial intelligence"}, "keywords": {"code editor", "ide", "coding", "developer", "database", "local ai"}},
    "design": {"label": "Design and image creation", "categories": {"design and graphics", "artificial intelligence"}, "keywords": {"design", "photo editing", "illustration", "graphics", "ui", "image"}},
    "video": {"label": "Video and audio production", "categories": {"video and animation", "audio and music"}, "keywords": {"video editing", "recording", "audio", "animation", "production"}},
    "productivity": {"label": "Productivity and organization", "categories": {"productivity", "office and documents", "communication"}, "keywords": {"productivity", "tasks", "notes", "calendar", "collaboration", "workflow"}},
    "privacy": {"label": "Privacy and local-first work", "categories": {"cybersecurity", "browsers and internet", "artificial intelligence"}, "keywords": {"privacy", "encryption", "local ai", "self hosted", "offline", "security"}},
}
RECOMMENDATION_WEIGHTS = {"purpose": 38, "platform": 18, "budget": 14, "hardware": 12, "experience": 8, "privacy": 6, "offline": 4}


def parse_recommendation_preferences(args):
    purpose = normalize_text(args.get("purpose", "")); platform = normalize_platform(args.get("platform", "")); budget = normalize_text(args.get("budget", "")); hardware = normalize_text(args.get("hardware", "")); experience = normalize_text(args.get("experience", "")); privacy = normalize_text(args.get("privacy", "")); offline = args.get("offline") == "1"
    return {"purpose": purpose if purpose in RECOMMENDATION_PURPOSES else "", "platform": platform, "budget": budget if budget in {"free", "freemium", "paid", "any"} else "", "hardware": hardware if hardware in {"light", "medium", "heavy", "any"} else "", "experience": experience if experience in {"beginner", "intermediate", "advanced", "any"} else "", "privacy": privacy if privacy in {"standard", "privacy-first", "open-source", "any"} else "", "offline": offline}


def recommendation_requested(preferences):
    return any(value for key, value in preferences.items() if key != "offline") or preferences["offline"]


def _tool_text_values(tool):
    values = [tool.get("name", ""), tool.get("description", ""), tool.get("category", ""), tool.get("subcategory", ""), *tool.get("tags", []), *tool.get("target_users", [])]
    return " ".join(normalize_text(value) for value in values)


def platform_label(value):
    return {"windows": "Windows", "macos": "macOS", "linux": "Linux", "android": "Android", "ios": "iOS", "web": "Web"}.get(value, value.title())


def score_recommendation(tool, preferences):
    score = 0; possible = 0; reasons = []; concerns = []; tool_text = _tool_text_values(tool)
    purpose = preferences["purpose"]
    if purpose:
        possible += RECOMMENDATION_WEIGHTS["purpose"]; info = RECOMMENDATION_PURPOSES[purpose]; category = normalize_text(tool.get("category", "")); hits = [k for k in info["keywords"] if k in tool_text]
        if category in info["categories"]: score += 26; reasons.append(f"Category fit: {tool.get('category', 'Unknown')} directly supports your selected purpose.")
        if hits: score += min(12, len(hits) * 4); reasons.append("Relevant capabilities: " + ", ".join(hits[:3]) + ".")
        if category not in info["categories"] and not hits: concerns.append("Purpose mismatch: its main category and features do not directly match your selected task.")
    platform = preferences["platform"]
    if platform:
        possible += 18; platforms = {normalize_platform(v) for v in tool.get("platforms", [])}
        if platform in platforms: score += 18; reasons.append(f"Platform fit: supports {platform_label(platform)}.")
        else: concerns.append(f"Platform limitation: {platform_label(platform)} support is not listed.")
    budget = preferences["budget"]
    if budget and budget != "any":
        possible += 14; pricing = normalize_text(tool.get("pricing_type", tool.get("pricing", ""))); ok = {"free": pricing == "free", "freemium": pricing in {"free", "freemium"}, "paid": pricing in {"free", "freemium", "paid"}}[budget]
        if ok: score += 14; reasons.append(f"Budget fit: {pricing or 'listed'} pricing matches your preference.")
        else: concerns.append(f"Budget mismatch: {pricing or 'unknown'} pricing may exceed your preference.")
    hardware = preferences["hardware"]
    if hardware and hardware != "any":
        possible += 12; levels = {"light": 1, "medium": 2, "heavy": 3, "unknown": 4}; requested = levels[hardware]; tool_name = normalize_text(tool.get("system_level", "unknown")); level = levels.get(tool_name, 4); ram = tool.get("minimum_ram_gb")
        if level <= requested:
            score += 12; detail = f", minimum RAM {ram:g} GB" if isinstance(ram, (int, float)) and not isinstance(ram, bool) else ""; reasons.append(f"Hardware fit: {tool_name} system profile{detail}.")
        else: concerns.append(f"Hardware concern: its {tool_name} system profile may be demanding for your device.")
    experience = preferences["experience"]
    if experience and experience != "any":
        possible += 8; beginner = sum(t in tool_text for t in {"simple", "easy", "beginner", "students", "intuitive"}); advanced = sum(t in tool_text for t in {"professional", "advanced", "developer", "technical", "enterprise", "ide"})
        if experience == "beginner" and (beginner or not advanced): score += 8; reasons.append("Experience fit: the workflow appears approachable for beginners.")
        elif experience == "advanced" and advanced: score += 8; reasons.append("Experience fit: professional or technical features suit advanced users.")
        elif experience == "intermediate": score += 6 if advanced <= 2 else 4; reasons.append("Experience fit: feature depth is suitable for intermediate users.")
        else: concerns.append("Learning-curve concern: the tool may not align with your experience level.")
    privacy = preferences["privacy"]
    if privacy and privacy != "any":
        possible += 6
        if privacy == "open-source" and tool.get("open_source"): score += 6; reasons.append("Privacy fit: the tool is open source.")
        elif privacy == "privacy-first" and (tool.get("offline") or tool.get("open_source") or "privacy" in tool_text): score += 6; reasons.append("Privacy fit: offline, open-source or privacy-focused traits are listed.")
        elif privacy == "standard": score += 4
        else: concerns.append("Privacy mismatch: the listed traits do not strongly match your preference.")
    if preferences["offline"]:
        possible += 4
        if tool.get("offline"): score += 4; reasons.append("Offline fit: can be used without a permanent internet connection.")
        else: concerns.append("Offline limitation: offline use is not listed.")
    percentage = min(100, round((score / max(1, possible)) * 100))
    return {"tool": tool, "score": score, "match": percentage, "reasons": reasons[:4], "concerns": concerns[:3]}


def recommend_tools(tools, preferences, limit=12):
    items = [score_recommendation(tool, preferences) for tool in tools]
    items.sort(key=lambda item: (item["match"], item["score"], item["tool"].get("rating", 0), item["tool"].get("popularity_score", 0)), reverse=True)
    return items[:limit]
