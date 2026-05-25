from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Session, DeclarativeBase
import json


class Base(DeclarativeBase):
    pass


# Defining database models

class Suggestion(Base):
    __tablename__      = "suggestions"
    id                 = Column(Integer, primary_key=True)
    created_at         = Column(DateTime, default=datetime.utcnow)
    content            = Column(String, nullable=False)
    category           = Column(String, nullable=False)
    vibe               = Column(String)
    price_tier         = Column(String)
    neighborhood        = Column(String)
    indoor_outdoor     = Column(String)
    tags               = Column(JSON)
    source             = Column(String)
    was_completed      = Column(Boolean, nullable=True)
    show_at            = Column(DateTime, nullable=True)

class Feedback(Base):
    __tablename__      = "feedback"
    id                 = Column(Integer, primary_key=True)
    suggestion_id      = Column(Integer, ForeignKey("suggestions.id"), nullable=False)
    rating             = Column(Float, nullable=False)
    created_at         = Column(DateTime, default=datetime.utcnow)

class CategoryLog(Base):
    __tablename__      = "category_log"
    id                 = Column(Integer, primary_key=True)
    tag                = Column(String, unique=True, nullable=False)
    last_suggested     = Column(DateTime, nullable=False)
    suggestion_count   = Column(Integer, default=0)

class Preference(Base):
    __tablename__      = "preferences"
    id                 = Column(Integer, primary_key=True)
    key                = Column(String, unique=True, nullable=False)
    value              = Column(String, nullable=False)
    weight             = Column(Float, default=1.0)
    updated_at         = Column(DateTime, default=datetime.utcnow)

class SearchCache(Base):
    __tablename__      = "search_cache"
    id                 = Column(Integer, primary_key=True)
    query              = Column(String, unique=True, nullable=False)
    result_json        = Column(JSON, nullable=False)
    cached_at          = Column(DateTime, nullable=False)

engine = create_engine("sqlite:///date_agent.db")
Base.metadata.create_all(engine)

