from sqlalchemy.orm import Session
from sqlalchemy import desc

from . import models


def get_all_games_with_scores(db: Session, limit: int = 50, offset: int = 0):
    q = (
        db.query(models.Game, models.GameRageScore)
        .join(models.GameRageScore, models.Game.id == models.GameRageScore.game_id)
        .order_by(desc(models.GameRageScore.rage_score))
        .limit(limit)
        .offset(offset)
    )
    rows = q.all()
    results = []
    for game, score in rows:
        results.append(
            {
                "id": game.id,
                "name": game.name,
                "slug": game.slug,
                "rage_score": score.rage_score,
            }
        )
    return results


def get_game_detail(db: Session, game_id: int):
    row = (
        db.query(models.Game, models.GameRageScore)
        .join(models.GameRageScore, models.Game.id == models.GameRageScore.game_id)
        .filter(models.Game.id == game_id)
        .first()
    )
    if not row:
        return None
    game, score = row
    return {
        "id": game.id,
        "name": game.name,
        "slug": game.slug,
        "rage": {
            "rage_score": score.rage_score,
            "difficulty_rage": score.difficulty_rage,
            "technical_rage": score.technical_rage,
            "social_toxicity_rage": score.social_toxicity_rage,
            "ui_design_rage": score.ui_design_rage,
            "max_achievement_drop": score.max_achievement_drop,
            "max_drop_from": score.max_drop_from,
            "max_drop_to": score.max_drop_to,
            "max_drop_achievement": score.max_drop_achievement,
        },
    }


def get_game_by_slug(db: Session, slug: str):
    return db.query(models.Game).filter(models.Game.slug == slug).first()


def get_game_scores_by_slug(db: Session, slug: str):
    game = get_game_by_slug(db, slug)
    if not game or not game.rage_score:
        return None
    score = game.rage_score
    return {
        "id": game.id,
        "name": game.name,
        "slug": game.slug,
        "rage": {
            "rage_score": score.rage_score,
            "difficulty_rage": score.difficulty_rage,
            "technical_rage": score.technical_rage,
            "social_toxicity_rage": score.social_toxicity_rage,
            "ui_design_rage": score.ui_design_rage,
            "max_achievement_drop": score.max_achievement_drop,
            "max_drop_from": score.max_drop_from,
            "max_drop_to": score.max_drop_to,
            "max_drop_achievement": score.max_drop_achievement,
        },
    }


def get_game_scores_by_id(db: Session, game_id: int):
    return get_game_detail(db, game_id)

from sqlalchemy import desc, asc


def list_games_by_rage_score(db: Session, limit: int = 50, offset: int = 0):
    return get_all_games_with_scores(db, limit=limit, offset=offset)


def list_games_by_difficulty(db: Session, limit: int = 50):
    q = (
        db.query(models.Game, models.GameRageScore)
        .join(models.GameRageScore, models.Game.id == models.GameRageScore.game_id)
        .order_by(desc(models.GameRageScore.difficulty_rage))
        .limit(limit)
    )
    rows = q.all()
    return [
        {
            "id": g.id,
            "name": g.name,
            "slug": g.slug,
            "rage_score": s.difficulty_rage,
        }
        for g, s in rows
    ]


def list_games_by_technical(db: Session, limit: int = 50):
    q = (
        db.query(models.Game, models.GameRageScore)
        .join(models.GameRageScore, models.Game.id == models.GameRageScore.game_id)
        .order_by(desc(models.GameRageScore.technical_rage))
        .limit(limit)
    )
    rows = q.all()
    return [
        {
            "id": g.id,
            "name": g.name,
            "slug": g.slug,
            "rage_score": s.technical_rage,
        }
        for g, s in rows
    ]


def list_games_by_toxicity(db: Session, limit: int = 50):
    q = (
        db.query(models.Game, models.GameRageScore)
        .join(models.GameRageScore, models.Game.id == models.GameRageScore.game_id)
        .order_by(desc(models.GameRageScore.social_toxicity_rage))
        .limit(limit)
    )
    rows = q.all()
    return [
        {
            "id": g.id,
            "name": g.name,
            "slug": g.slug,
            "rage_score": s.social_toxicity_rage,
        }
        for g, s in rows
    ]


def list_coziest_games(db: Session, limit: int = 50):
    """Lowest overall RageScore = coziest games."""
    q = (
        db.query(models.Game, models.GameRageScore)
        .join(models.GameRageScore, models.Game.id == models.GameRageScore.game_id)
        .order_by(asc(models.GameRageScore.rage_score))
        .limit(limit)
    )
    rows = q.all()
    return [
        {
            "id": g.id,
            "name": g.name,
            "slug": g.slug,
            "rage_score": s.rage_score,
        }
        for g, s in rows
    ]

