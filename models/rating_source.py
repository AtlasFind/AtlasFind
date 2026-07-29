from dataclasses import dataclass

@dataclass(frozen=True)
class RatingSource:
    source_id: str
    source_type: str
    name: str
    url: str
    publisher: str
    checked_at: str
    status: str = "active"
