"""Canonical values used by the AtlasFind v1.0.2 catalog."""

from __future__ import annotations

CATALOG_SCHEMA_VERSION = "1.0.2"

PUBLICATION_STATUSES = {"published", "draft", "pending_review", "rejected", "archived"}
VERIFICATION_STATUSES = {"verified", "partially_verified", "pending", "rejected"}
PRICING_MODELS = {"free", "freemium", "paid", "subscription", "lifetime", "enterprise", "open_source"}
PLATFORMS = {
    "windows", "linux", "macos", "android", "ios", "ipados", "web", "chrome",
    "edge", "firefox", "api", "docker", "self_hosted", "desktop", "mobile", "cloud",
}
SECURITY_STANDARDS = {"gdpr", "kvkk", "soc2", "iso27001", "hipaa", "pci_dss"}
AUDIENCES = {
    "individual", "student", "freelancer", "agency", "startup", "enterprise",
    "developer", "designer", "marketer", "researcher", "content_creator", "educator",
}
TECHNICAL_FEATURES = {
    "api", "plugins", "integrations", "export", "import", "cloud_sync", "multi_user",
    "sso", "webhook", "cli", "sdk", "rest_api", "graphql", "local_execution", "offline",
}
AI_FEATURES = {
    "text_generation", "code_generation", "image_generation", "video_generation",
    "audio_generation", "translation", "speech_recognition", "document_analysis",
    "summarization", "code_completion", "automation", "workflow",
}
