"""Privacy-conscious user review persistence for the future public voting UI."""
from __future__ import annotations
import hashlib, json
from database import DATABASE_PATH, connect_database, transaction
from services.rating_service import bayesian_user_score


def anonymous_user_key(secret: str, account_or_session: str) -> str:
    return hashlib.sha256(f"{secret}:{account_or_session}".encode("utf-8")).hexdigest()


def upsert_review(tool_slug, user_key_hash, score, criteria=None, comment="", risk_score=0, status=None, path=DATABASE_PATH):
    if not isinstance(score,(int,float)) or isinstance(score,bool) or not 0 <= score <= 10:
        raise ValueError("score must be between 0 and 10")
    clean_comment=str(comment or "").strip()[:2000]
    if status not in {None, "pending", "verified", "flagged", "rejected"}:
        raise ValueError("invalid review status")
    status = status or ("flagged" if risk_score >= 60 else "pending")
    with transaction(path) as connection:
        connection.execute("""INSERT INTO user_reviews(tool_slug,user_key_hash,score,criteria_json,comment,status,risk_score)
        VALUES(?,?,?,?,?,?,?) ON CONFLICT(tool_slug,user_key_hash) DO UPDATE SET score=excluded.score,criteria_json=excluded.criteria_json,comment=excluded.comment,status=excluded.status,risk_score=excluded.risk_score,updated_at=CURRENT_TIMESTAMP""",
        (tool_slug,user_key_hash,float(score),json.dumps(criteria or {},ensure_ascii=False),clean_comment,status,int(risk_score)))


def aggregate_user_rating(tool_slug, path=DATABASE_PATH):
    with connect_database(path) as connection:
        row=connection.execute("SELECT COALESCE(SUM(score),0) AS total,COUNT(*) AS count FROM user_reviews WHERE tool_slug=? AND status='verified'",(tool_slug,)).fetchone()
    count=int(row['count']); score=bayesian_user_score(float(row['total']),count)
    return {"score":score,"review_count":count,"verified_count":count}
