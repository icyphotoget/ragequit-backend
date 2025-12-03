import re
import datetime as dt
from collections import Counter

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from . import schemas, crud, models

# -------------------------------------------------------------------
# APP + DB BOOTSTRAP
# -------------------------------------------------------------------

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RageQuit.io API",
    description="Backend for RageQuit.io – game rage scores",
    version="0.1.0",
)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# GAMES
# -------------------------------------------------------------------


@app.get("/games", response_model=list[schemas.GameSummary])
def list_games(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    games = crud.get_all_games_with_scores(db, limit=limit, offset=offset)
    return [schemas.GameSummary(**g) for g in games]


@app.get("/games/{game_id}", response_model=schemas.GameDetail)
def get_game(game_id: int, db: Session = Depends(get_db)):
    game = crud.get_game_detail(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return schemas.GameDetail(**game)


@app.get("/games/slug/{slug}", response_model=schemas.GameDetail)
def get_game_by_slug(slug: str, db: Session = Depends(get_db)):
    data = crud.get_game_scores_by_slug(db, slug)
    if not data:
        raise HTTPException(status_code=404, detail="Game not found")
    return schemas.GameDetail(**data)


# -------------------------------------------------------------------
# RAGE WORD CLOUD
# -------------------------------------------------------------------


@app.get(
    "/games/{game_id}/rage-words",
    response_model=list[schemas.RageWordOut],
)
def get_game_rage_words(
    game_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    reviews = (
        db.query(models.SteamReviewRaw)
        .filter(models.SteamReviewRaw.game_id == game_id)
        .all()
    )
    texts: list[str] = []
    for r in reviews:
        if r.review_text:
            texts.append(r.review_text)

    reddit_posts = (
        db.query(models.RedditPostRaw)
        .filter(models.RedditPostRaw.game_id == game_id)
        .all()
    )
    for p in reddit_posts:
        chunk = ""
        if p.title:
            chunk += p.title + " "
        if p.body:
            chunk += p.body
        if chunk:
            texts.append(chunk)

    full_text = " ".join(texts).lower()

    tokens = re.findall(r"[a-zA-Z]+", full_text)

    stopwords = {
        "the",
        "and",
        "for",
        "you",
        "your",
        "with",
        "that",
        "this",
        "have",
        "but",
        "not",
        "are",
        "was",
        "were",
        "they",
        "them",
        "get",
        "got",
        "just",
        "like",
        "its",
        "from",
        "been",
        "will",
        "what",
        "when",
        "where",
        "who",
        "why",
        "how",
        "does",
        "did",
        "can",
        "cant",
        "could",
        "should",
        "would",
        "all",
        "any",
        "some",
        "into",
        "about",
        "more",
        "very",
        "really",
        "also",
        "than",
        "then",
        "there",
        "here",
        "out",
        "over",
        "under",
        "game",
        "games",
        "play",
        "played",
        "playing",
        "one",
        "two",
        "three",
        "still",
        "even",
        "because",
        "good",
        "great",
        "fun",
        "love",
        "enjoy",
        "enjoyed",
        "well",
        "time",
        "hours",
        "hour",
        "make",
        "made",
    }

    filtered = [t for t in tokens if len(t) >= 4 and t not in stopwords]

    counter = Counter(filtered)
    if not counter:
        return []

    most_common = counter.most_common(limit)
    max_count = most_common[0][1]

    result: list[schemas.RageWordOut] = []
    for word, count in most_common:
        score = (count / max_count) * 100.0
        result.append(schemas.RageWordOut(word=word, score=score))

    return result


# -------------------------------------------------------------------
# RAGE FEED: STEAM + REDDIT
# -------------------------------------------------------------------


@app.get(
    "/games/{game_id}/reviews",
    response_model=list[schemas.SteamReviewOut],
)
def get_game_reviews(
    game_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    rows = (
        db.query(models.SteamReviewRaw)
        .filter(models.SteamReviewRaw.game_id == game_id)
        .order_by(models.SteamReviewRaw.created_at_steam.desc())
        .limit(limit)
        .all()
    )

    return [
        schemas.SteamReviewOut(
            is_positive=r.is_positive,
            language=r.language,
            review_text=r.review_text or "",
            created_at_steam=r.created_at_steam,
        )
        for r in rows
    ]


@app.get(
    "/games/{game_id}/reddit",
    response_model=list[schemas.RedditPostOut],
)
def get_game_reddit(
    game_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    rows = (
        db.query(models.RedditPostRaw)
        .filter(models.RedditPostRaw.game_id == game_id)
        .order_by(models.RedditPostRaw.upvotes.desc())
        .limit(limit)
        .all()
    )

    return [
        schemas.RedditPostOut(
            title=p.title or "",
            body=p.body or "",
            upvotes=p.upvotes,
            num_comments=p.num_comments,
            created_utc=p.created_utc,
        )
        for p in rows
    ]


# -------------------------------------------------------------------
# RAGE TIMELINE
# -------------------------------------------------------------------


@app.get(
    "/games/{game_id}/rage-timeline",
    response_model=list[schemas.RageTimelinePoint],
)
def get_game_rage_timeline(
    game_id: int,
    db: Session = Depends(get_db),
):
    rows = (
        db.query(models.SteamReviewRaw)
        .filter(models.SteamReviewRaw.game_id == game_id)
        .all()
    )

    buckets: dict[dt.date, dict[str, int]] = {}
    for r in rows:
        ts = r.created_at_steam or r.ingested_at
        if not ts:
            continue
        day = ts.date()
        if day not in buckets:
            buckets[day] = {"pos": 0, "neg": 0}
        if r.is_positive:
            buckets[day]["pos"] += 1
        else:
            buckets[day]["neg"] += 1

    points: list[schemas.RageTimelinePoint] = []
    for day in sorted(buckets.keys()):
        pos = buckets[day]["pos"]
        neg = buckets[day]["neg"]
        total = pos + neg
        rage_score = (neg / total) * 100.0 if total > 0 else 0.0
        points.append(
            schemas.RageTimelinePoint(
                date=day,
                rage_score=rage_score,
                positive=pos,
                negative=neg,
                total=total,
            )
        )

    return points


# -------------------------------------------------------------------
# RAGE CLIPS
# -------------------------------------------------------------------


@app.get(
    "/games/{game_id}/clips",
    response_model=list[schemas.RageClipOut],
)
def get_game_clips(
    game_id: int,
    db: Session = Depends(get_db),
):
    rows = (
        db.query(models.RageClip)
        .filter(models.RageClip.game_id == game_id)
        .order_by(models.RageClip.added_at.desc())
        .all()
    )
    return rows


# -------------------------------------------------------------------
# LEADERBOARDS
# -------------------------------------------------------------------


@app.get("/leaderboards/most-rage", response_model=list[schemas.GameSummary])
def leaderboard_most_rage(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    games = crud.get_all_games_with_scores(db, limit=limit, offset=0)
    return [schemas.GameSummary(**g) for g in games]


@app.get("/leaderboards/difficulty", response_model=list[schemas.GameSummary])
def leaderboard_difficulty(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    games = crud.list_games_by_difficulty(db, limit=limit)
    return [schemas.GameSummary(**g) for g in games]


@app.get("/leaderboards/technical", response_model=list[schemas.GameSummary])
def leaderboard_technical(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    games = crud.list_games_by_technical(db, limit=limit)
    return [schemas.GameSummary(**g) for g in games]


@app.get("/leaderboards/toxicity", response_model=list[schemas.GameSummary])
def leaderboard_toxicity(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    games = crud.list_games_by_toxicity(db, limit=limit)
    return [schemas.GameSummary(**g) for g in games]


@app.get("/leaderboards/cozy", response_model=list[schemas.GameSummary])
def leaderboard_cozy(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    games = crud.list_coziest_games(db, limit=limit)
    return [schemas.GameSummary(**g) for g in games]


# -------------------------------------------------------------------
# GAME COMPARISON
# -------------------------------------------------------------------


@app.get("/compare", response_model=schemas.GameComparison)
def compare_games(a: int, b: int, db: Session = Depends(get_db)):
  ga = crud.get_game_scores_by_id(db, a)
  gb = crud.get_game_scores_by_id(db, b)
  if not ga or not gb:
      raise HTTPException(status_code=404, detail="One or both games not found")

  return schemas.GameComparison(
      left=schemas.GameDetail(**ga),
      right=schemas.GameDetail(**gb),
  )
