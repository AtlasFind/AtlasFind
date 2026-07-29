"""Rating data contracts used by JSON today and SQL repositories later."""
from dataclasses import dataclass

@dataclass(frozen=True)
class RatingSummary:
    status: str
    overall_score: float | None
    methodology_version: str
    category_profile: str
    confidence_score: int
    confidence_level: str
