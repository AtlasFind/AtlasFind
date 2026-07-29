from services.rating_service import evaluate_rating, load_rating_config, profile_weights


def validate_rating_profiles():
    errors = []
    for name in load_rating_config().get("profiles", {}):
        try:
            profile_weights(name)
        except ValueError as exc:
            errors.append(str(exc))
    return errors


def validate_tool_rating(tool):
    rating = tool.get("rating_v103") or {}
    if not rating:
        return []
    result = evaluate_rating(rating, str(tool.get("category") or ""))
    return list(result.errors)
