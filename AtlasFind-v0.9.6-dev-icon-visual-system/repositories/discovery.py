from .tools import get_all_tools


def get_tools_by_category(category_slug):
    return [tool for tool in get_all_tools() if str(tool.get("category", "")).lower().replace(" ", "-") == category_slug]


def get_collection_tools(collection_slug):
    return [tool for tool in get_all_tools() if collection_slug in tool.get("collections", [])]
