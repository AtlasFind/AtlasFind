from dataclasses import dataclass

@dataclass(frozen=True)
class UserReviewSummary:
    score: float | None
    review_count: int
    verified_count: int
