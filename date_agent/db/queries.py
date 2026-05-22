from sqlalchemy.orm import Session

def save_suggestion(content, category, vibe, price_tier, neighborhood, indoor_outdoor, tags, source):
    with Session(engine) as session:
        suggestion = Suggestions(
            content=content,
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

def get_recent_suggestions(n):
    with Session(engine) as session:
        return session.query(Suggestions).order_by(Suggestions.created_at.desc()).limit(n).all()

def save_feedback(suggestion_id, rating):
    with Session(engine) as session:
        feedback = Feedback(
            suggestion_id=suggestion_id,
            rating=rating
        )
        session.add(feedback)
        session.commit()
        return feedback.id

def get_feedback_for_suggestion(suggestion_id):
    with Session(engine) as session:
        return session.query(Feedback).filter(Feedback.suggestion_id == suggestion_id).all()