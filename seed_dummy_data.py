from sqlalchemy.orm import Session

from app.database import Base, engine, SessionLocal
from app import models
from datetime import datetime


def seed():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    # Clear existing for repeatability in dev
    db.query(models.SteamReviewRaw).delete()
    db.query(models.SteamAchievementRaw).delete()
    db.query(models.GameRageScore).delete()
    db.query(models.Game).delete()
    db.commit()

    games = [
        models.Game(name="Elden Ring", slug="elden-ring", steam_app_id=1245620),
        models.Game(name="Cuphead", slug="cuphead", steam_app_id=268910),
        models.Game(name="Stardew Valley", slug="stardew-valley", steam_app_id=413150),
    ]
    db.add_all(games)
    db.commit()

    # Refresh objects with IDs
    for g in games:
        db.refresh(g)

    # Fake reviews (Elden Ring – very ragey)
    elden = games[0]
    er_reviews = [
        models.SteamReviewRaw(
            game_id=elden.id,
            steam_review_id=f"er_{i}",
            is_positive=False,
            language="en",
            review_text=txt,
            created_at_steam=datetime.utcnow(),
        )
        for i, txt in enumerate(
            [
                "This game is pure bullshit. Unfair bosses, impossible rng, I rage quit.",
                "Laggy mess on my PC, crashes at Malenia every time.",
                "Amazing but cheap boss design, controller through the wall levels of rage.",
                "Uninstalling after yet another crash during a boss fight.",
            ],
            start=1,
        )
    ]

    # Cuphead – also ragey but a bit less
    cup = games[1]
    cup_reviews = [
        models.SteamReviewRaw(
            game_id=cup.id,
            steam_review_id=f"cup_{i}",
            is_positive=False,
            language="en",
            review_text=txt,
            created_at_steam=datetime.utcnow(),
        )
        for i, txt in enumerate(
            [
                "Beautiful but unfair as hell. Bullshit boss patterns.",
                "Rage quit after 3 hours on one boss.",
                "Controls are fine but difficulty is insane.",
            ],
            start=1,
        )
    ]

    # Stardew – chill
    sv = games[2]
    sv_reviews = [
        models.SteamReviewRaw(
            game_id=sv.id,
            steam_review_id=f"sv_{i}",
            is_positive=True,
            language="en",
            review_text=txt,
            created_at_steam=datetime.utcnow(),
        )
        for i, txt in enumerate(
            [
                "Most relaxing game ever.",
                "Cozy farming, zero rage.",
                "Great chill game, no unfair stuff.",
            ],
            start=1,
        )
    ]

    db.add_all(er_reviews + cup_reviews + sv_reviews)

    # Fake achievements with dropoffs
    er_ach = [
        models.SteamAchievementRaw(
            game_id=elden.id,
            api_name="start_game",
            display_name="First Steps",
            percent=85.0,
        ),
        models.SteamAchievementRaw(
            game_id=elden.id,
            api_name="beat_margit",
            display_name="Margit Felled",
            percent=60.0,
        ),
        models.SteamAchievementRaw(
            game_id=elden.id,
            api_name="beat_malenia",
            display_name="Defeat Malenia",
            percent=18.0,
        ),
    ]
    cup_ach = [
        models.SteamAchievementRaw(
            game_id=cup.id,
            api_name="tutorial",
            display_name="Finish Tutorial",
            percent=90.0,
        ),
        models.SteamAchievementRaw(
            game_id=cup.id,
            api_name="first_island",
            display_name="First Isle",
            percent=55.0,
        ),
        models.SteamAchievementRaw(
            game_id=cup.id,
            api_name="final_boss",
            display_name="Final Boss",
            percent=10.0,
        ),
    ]
    sv_ach = [
        models.SteamAchievementRaw(
            game_id=sv.id,
            api_name="start_farm",
            display_name="New Farmer",
            percent=80.0,
        ),
        models.SteamAchievementRaw(
            game_id=sv.id,
            api_name="first_year",
            display_name="One Year In",
            percent=60.0,
        ),
        models.SteamAchievementRaw(
            game_id=sv.id,
            api_name="community_center",
            display_name="Community Restored",
            percent=40.0,
        ),
    ]

    db.add_all(er_ach + cup_ach + sv_ach)
    db.commit()
    db.close()
    print("Seeded dummy data.")


if __name__ == "__main__":
    seed()
