from datetime import datetime
from app.database import SessionLocal, Base, engine
from app import models

CLIPS = [
    {
        "game_slug": "elden-ring",
        "source": "youtube",
        "url": "https://www.youtube.com/watch?v=1X5Y7G2s0nI",
        "title": "Streamer loses it on Malenia",
    },
    {
        "game_slug": "elden-ring",
        "source": "youtube",
        "url": "https://www.youtube.com/watch?v=aGnyj2bXcJw",
        "title": "Top 10 Elden Ring rage moments",
    },
]

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for clip in CLIPS:
            game = (
                db.query(models.Game)
                .filter(models.Game.slug == clip["game_slug"])
                .first()
            )
            if not game:
                continue
            exists = (
                db.query(models.RageClip)
                .filter(
                    models.RageClip.game_id == game.id,
                    models.RageClip.url == clip["url"],
                )
                .first()
            )
            if exists:
                continue
            row = models.RageClip(
                game_id=game.id,
                source=clip["source"],
                url=clip["url"],
                title=clip["title"],
                added_at=datetime.utcnow(),
            )
            db.add(row)
        db.commit()
        print("Seeded rage clips.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
