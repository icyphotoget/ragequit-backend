from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, Base
from app import models
from app.scoring import (
    score_reviews_for_game,
    score_achievements_for_game,
    combine_rage_scores,
)
from datetime import datetime


def compute_all_scores():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    games = db.query(models.Game).all()
    for game in games:
       # Steam reviews
        reviews = [
            {
                "is_positive": r.is_positive,
                "review_text": r.review_text,
            }
            for r in game.reviews
        ]

        # Reddit posts – treat as negative-leaning feedback because they came from rage-focused search
        reddit_posts = (
            db.query(models.RedditPostRaw)
            .filter(models.RedditPostRaw.game_id == game.id)
            .all()
        )
        for p in reddit_posts:
            text = (p.title or "") + "\n" + (p.body or "")
            reviews.append(
                {
                    "is_positive": False,
                    "review_text": text,
                }
            )
        achievements = [
            {
                "api_name": a.api_name,
                "display_name": a.display_name,
                "percent": a.percent,
            }
            for a in game.achievements
        ]

        review_scores = score_reviews_for_game(reviews)
        ach_scores = score_achievements_for_game(achievements)
        combined = combine_rage_scores(review_scores, ach_scores)

        existing = (
            db.query(models.GameRageScore)
            .filter(models.GameRageScore.game_id == game.id)
            .first()
        )

        if not existing:
            existing = models.GameRageScore(game_id=game.id)

        existing.rage_score = combined["rage_score"]
        existing.difficulty_rage = combined["difficulty_rage"]
        existing.technical_rage = combined["technical_rage"]
        existing.social_toxicity_rage = combined["social_toxicity_rage"]
        existing.ui_design_rage = combined["ui_design_rage"]
        existing.max_achievement_drop = combined["max_achievement_drop"]
        existing.max_drop_from = combined["max_drop_from"]
        existing.max_drop_to = combined["max_drop_to"]
        existing.max_drop_achievement = combined["max_drop_achievement"]
        existing.last_computed_at = datetime.utcnow()

        db.merge(existing)

    db.commit()
    db.close()
    print("Computed rage scores for all games.")


if __name__ == "__main__":
    compute_all_scores()
