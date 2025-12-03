from typing import List, Dict
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.database import Base, engine, SessionLocal
from app import models
from app.models import RedditPostRaw
from app.steam_api import fetch_steam_reviews, fetch_global_achievements
from app.reddit_api import fetch_reddit_posts_for_game


# 🔥 Games we track – add more Steam app IDs here
GAMES_TO_TRACK: List[Dict] = [
    {
        "steam_app_id": 1245620,
        "name": "ELDEN RING",
        "slug": "elden-ring",
    },
    {
        "steam_app_id": 268910,
        "name": "Cuphead",
        "slug": "cuphead",
    },
    {
        "steam_app_id": 413150,
        "name": "Stardew Valley",
        "slug": "stardew-valley",
    },
    {
        "steam_app_id": 374320,
        "name": "Dark Souls III",
        "slug": "dark-souls-3",
    },
    {
        "steam_app_id": 1091500,
        "name": "Cyberpunk 2077",
        "slug": "cyberpunk-2077",
    },
]


def slugify(name: str) -> str:
    """Very simple slugify helper."""
    import re

    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def upsert_game(db: Session, info: Dict) -> models.Game:
    game = (
        db.query(models.Game)
        .filter(models.Game.steam_app_id == info["steam_app_id"])
        .first()
    )

    if game is None:
        game = models.Game(
            steam_app_id=info["steam_app_id"],
            name=info["name"],
            slug=info.get("slug") or slugify(info["name"]),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(game)
        db.commit()
        db.refresh(game)
        print(f"[GAME] Created game {game.name} (id={game.id})")
    else:
        updated = False
        if game.name != info["name"]:
            game.name = info["name"]
            updated = True
        desired_slug = info.get("slug") or slugify(info["name"])
        if game.slug != desired_slug:
            game.slug = desired_slug
            updated = True
        if updated:
            game.updated_at = datetime.now(timezone.utc)
            db.commit()
            print(f"[GAME] Updated game {game.name} (id={game.id})")

    return game


def ingest_reviews_for_game(db: Session, game: models.Game, app_id: int):
    """Fetch Steam reviews and store them, skipping duplicates."""
    reviews = fetch_steam_reviews(
        app_id,
        max_pages=15,
        num_per_page=100,
        filter_type="all",
    )

    new_rows = 0
    skipped = 0

    for r in reviews:
        review_id = str(r.get("recommendationid"))
        if not review_id:
            continue

        # Check for duplicates
        exists = (
            db.query(models.SteamReviewRaw)
            .filter(
                models.SteamReviewRaw.game_id == game.id,
                models.SteamReviewRaw.steam_review_id == review_id,
            )
            .first()
        )

        if exists:
            skipped += 1
            continue

        # Extract fields
        review_text = r.get("review", "") or ""
        is_positive = bool(r.get("voted_up", False))
        language = r.get("language") or None
        ts = r.get("timestamp_created")

        if isinstance(ts, (int, float)):
            created_at_steam = datetime.fromtimestamp(ts, tz=timezone.utc)
        else:
            created_at_steam = None

        # Insert row safely (no batching)
        row = models.SteamReviewRaw(
            game_id=game.id,
            steam_review_id=review_id,
            is_positive=is_positive,
            language=language,
            review_text=review_text,
            created_at_steam=created_at_steam,
        )

        db.add(row)
        db.flush()   # ← THIS IS THE IMPORTANT FIX
        new_rows += 1

    db.commit()
    print(
        f"[DB] Stored {new_rows} new reviews, skipped {skipped} duplicates for {game.name}"
    )



def ingest_achievements_for_game(db: Session, game: models.Game, app_id: int):
    """Fetch global achievement percentages and store/update them."""
    achievements = fetch_global_achievements(app_id)

    updated = 0
    inserted = 0

    for a in achievements:
        api_name = a.get("name")
        if not api_name:
            continue

        percent = float(a.get("percent", 0.0))

        existing = (
            db.query(models.SteamAchievementRaw)
            .filter(
                models.SteamAchievementRaw.game_id == game.id,
                models.SteamAchievementRaw.api_name == api_name,
            )
            .first()
        )

        if existing:
            existing.percent = percent
            existing.ingested_at = datetime.now(timezone.utc)
            updated += 1
        else:
            row = models.SteamAchievementRaw(
                game_id=game.id,
                api_name=api_name,
                display_name=api_name,
                description=None,
                percent=percent,
            )
            db.add(row)
            inserted += 1

    db.commit()
    print(
        f"[DB] Achievements for {game.name}: inserted {inserted}, updated {updated}"
    )


def ingest_reddit_for_game(db: Session, game: models.Game):
    """Fetch Reddit posts about this game and store them."""
    posts = fetch_reddit_posts_for_game(
        game.name,
        max_pages=3,
        posts_per_page=25,
    )

    new_rows = 0
    skipped = 0

    for p in posts:
        reddit_id = p.get("id")
        if not reddit_id:
            continue

        existing = (
            db.query(RedditPostRaw)
            .filter(RedditPostRaw.reddit_id == reddit_id)
            .first()
        )
        if existing:
            skipped += 1
            continue

        title = p.get("title") or ""
        body = p.get("selftext") or ""
        upvotes = p.get("score")
        num_comments = p.get("num_comments")
        created_utc = p.get("created_utc")

        if isinstance(created_utc, (int, float)):
            created = datetime.fromtimestamp(created_utc, tz=timezone.utc)
        else:
            created = None

        row = RedditPostRaw(
            game_id=game.id,
            reddit_id=reddit_id,
            title=title,
            body=body,
            upvotes=upvotes,
            num_comments=num_comments,
            created_utc=created,
        )
        db.add(row)
        new_rows += 1

    db.commit()
    print(
        f"[DB] Stored {new_rows} new reddit posts, skipped {skipped} duplicates for {game.name}"
    )


def main():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        for info in GAMES_TO_TRACK:
            app_id = info["steam_app_id"]
            game = upsert_game(db, info)
            print(f"[INFO] Ingesting Steam data for {game.name} (app_id={app_id})")

            ingest_reviews_for_game(db, game, app_id)
            ingest_achievements_for_game(db, game, app_id)
            ingest_reddit_for_game(db, game)

    finally:
        db.close()
        print("[DONE] Steam + Reddit ingestion finished.")
        

if __name__ == "__main__":
    main()
