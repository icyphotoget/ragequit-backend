from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    steam_app_id = Column(Integer, unique=True, nullable=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    reviews = relationship("SteamReviewRaw", back_populates="game")
    achievements = relationship("SteamAchievementRaw", back_populates="game")
    rage_score = relationship(
        "GameRageScore",
        back_populates="game",
        uselist=False,
        cascade="all, delete-orphan",
    )


class SteamReviewRaw(Base):
    __tablename__ = "steam_reviews_raw"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    steam_review_id = Column(String, nullable=False)
    is_positive = Column(Boolean, nullable=False)
    language = Column(String, nullable=True)
    review_text = Column(String, nullable=True)
    created_at_steam = Column(DateTime, nullable=True)
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    game = relationship("Game", back_populates="reviews")

    __table_args__ = (
        UniqueConstraint("game_id", "steam_review_id", name="uq_game_review"),
    )


class SteamAchievementRaw(Base):
    __tablename__ = "steam_achievements_raw"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    api_name = Column(String, nullable=False)
    display_name = Column(String, nullable=True)
    description = Column(String, nullable=True)
    percent = Column(Float, nullable=False)
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    game = relationship("Game", back_populates="achievements")

    __table_args__ = (
        UniqueConstraint("game_id", "api_name", name="uq_game_achievement"),
    )

class RedditPostRaw(Base):
    __tablename__ = "reddit_posts_raw"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    reddit_id = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=True)
    body = Column(String, nullable=True)
    upvotes = Column(Integer, nullable=True)
    num_comments = Column(Integer, nullable=True)
    created_utc = Column(DateTime, nullable=True)
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    game = relationship("Game")

class GameRageScore(Base):
    __tablename__ = "game_rage_scores"

    game_id = Column(
        Integer, ForeignKey("games.id"), primary_key=True, nullable=False
    )
    rage_score = Column(Float, nullable=False)
    difficulty_rage = Column(Float, nullable=False)
    technical_rage = Column(Float, nullable=False)
    social_toxicity_rage = Column(Float, nullable=False)
    ui_design_rage = Column(Float, nullable=False)

    max_achievement_drop = Column(Float, nullable=True)
    max_drop_from = Column(Float, nullable=True)
    max_drop_to = Column(Float, nullable=True)
    max_drop_achievement = Column(String, nullable=True)

    last_computed_at = Column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    game = relationship("Game", back_populates="rage_score")
    
class RageClip(Base):
    __tablename__ = "rage_clips"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    source = Column(String, nullable=True)  # 'youtube', 'twitch', etc.
    url = Column(String, nullable=False)
    title = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    game = relationship("Game")
