from db.models import engine, Suggestion, Feedback, CategoryLog, SearchCache
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from config import SEARCH_CACHE_TTL_HOURS


def save_suggestion(
    content: str,
    category: str,
    vibe: str | None,
    price_tier: str | None,
    neighborhood: str | None,
    indoor_outdoor: str | None,
    tags: list[str],
    source: str | None,
) -> int:
    with Session(engine) as session:
        suggestion = Suggestion(
            content=content,
            category=category,
            vibe=vibe,
            price_tier=price_tier,
            neighborhood=neighborhood,
            indoor_outdoor=indoor_outdoor,
            tags=tags,
            source=source
        )
        session.add(suggestion)
        session.commit()
        return suggestion.id

def get_recent_suggestions(n:int=10):
    with Session(engine) as session:
        rows = session.query(Suggestion).order_by(Suggestion.created_at.desc()).limit(n).all()

        return [
            {
                "id":            r.id,
                "created_at":    r.created_at,
                "content":       r.content,
                "category":      r.category,
                "vibe":          r.vibe,
                "price_tier":    r.price_tier,
                "neighborhood":  r.neighborhood,
                "indoor_outdoor": r.indoor_outdoor,
                "tags":          r.tags,
                "source":        r.source,
                "was_completed": r.was_completed,
            }
            for r in rows
        ]

def save_feedback(suggestion_id: int, rating: float) -> int:
    with Session(engine) as session:
        feedback = Feedback(
            suggestion_id=suggestion_id,
            rating=rating
        )
        session.add(feedback)
        session.commit()
        return feedback.id

def get_feedback_for_suggestion(suggestion_id, n:int=10):
    with Session(engine) as session:
        rows = (
            session.query(Feedback)
            .filter(Feedback.suggestion_id == suggestion_id)
            .order_by(Feedback.created_at.desc())
            .limit(n)
            .all()
        )

        return [
            {
                "id":              r.id,
                "suggestion_id":   r.suggestion_id,
                "rating":          r.rating,
                "created_at":      r.created_at,
            }
            for r in rows
        ]

def update_category_log(tags: list[str]):
    with Session(engine) as session:
        for tag in tags:
            entry = session.query(CategoryLog).filter(CategoryLog.tag == tag).first()
            if entry:
                entry.last_suggested = datetime.utcnow()
                entry.suggestion_count += 1
            else:
                session.add(CategoryLog(
                    tag=tag,
                    last_suggested=datetime.utcnow(),
                    suggestion_count=1
                ))
        session.commit()

def get_category_log(tag):
    with Session(engine) as session:
        entry = (
            session.query(CategoryLog)
            .filter(CategoryLog.tag == tag)
            .first()
        )

        if not entry:
            return None

        return {
            "id":               entry.id,
            "tag":              entry.tag,
            "last_suggested":   entry.last_suggested,
            "suggestion_count": entry.suggestion_count,
        }

def get_cache(query):
    with Session(engine) as session:
        entry = session.query(SearchCache).filter(SearchCache.query == query).first()
        if entry:
            age = datetime.utcnow() - entry.cached_at
            if age < timedelta(hours=SEARCH_CACHE_TTL_HOURS):
                return entry.result_json
        return None

def save_cache(query, result_json):
    with Session(engine) as session:
        cache_entry = session.query(SearchCache).filter(SearchCache.query == query).first()
        if cache_entry:
            cache_entry.result_json = result_json
            cache_entry.cached_at = datetime.utcnow()
        else:
            cache_entry = SearchCache(
                query=query,
                result_json=result_json,
                cached_at=datetime.utcnow()
            )
            session.add(cache_entry)
        session.commit()