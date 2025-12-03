from typing import List, Dict, Optional

RAGE_KEYWORDS_DIFFICULTY = [
    "unfair", "bullshit", "cheap", "broken boss", "rng", "impossible",
    "controller through the wall", "rage quit", "rage-quit", "uninstall",
]

RAGE_KEYWORDS_TECH = [
    "lag", "stutter", "crash", "crashes", "freezes", "desync",
    "buggy", "bug", "stuttering", "memory leak", "dc", "disconnect",
]

RAGE_KEYWORDS_TOXIC = [
    "toxic", "grief", "troll", "smurf", "flaming", "slur", "rage in chat",
    "afk", "feeder", "cheater", "cheat", "hacker", "hackers",
]

RAGE_KEYWORDS_UI_DESIGN = [
    "clunky", "bad ui", "terrible ui", "awful controls", "unintuitive",
    "confusing", "jank", "janky", "trash design", "pay to win", "p2w",
]


def _count_keywords(text: str, keywords: List[str]) -> int:
    t = (text or "").lower()
    return sum(1 for kw in keywords if kw in t)


def score_reviews_for_game(reviews: List[Dict]) -> Dict[str, float]:
    """
    reviews: list of dicts like:
      {"is_positive": bool, "review_text": str}
    """
    if not reviews:
        return {
            "review_rage": 0.0,
            "difficulty_rage": 0.0,
            "technical_rage": 0.0,
            "social_toxicity_rage": 0.0,
            "ui_design_rage": 0.0,
        }

    total = len(reviews)
    rage_points_total = 0.0
    difficulty_points = 0.0
    tech_points = 0.0
    toxic_points = 0.0
    ui_points = 0.0

    for r in reviews:
        text = r.get("review_text") or ""
        base = 0.0

        if not r.get("is_positive", True):
            base += 1.0

        diff_hits = _count_keywords(text, RAGE_KEYWORDS_DIFFICULTY)
        tech_hits = _count_keywords(text, RAGE_KEYWORDS_TECH)
        toxic_hits = _count_keywords(text, RAGE_KEYWORDS_TOXIC)
        ui_hits = _count_keywords(text, RAGE_KEYWORDS_UI_DESIGN)

        diff_score = 0.6 * diff_hits
        tech_score = 0.5 * tech_hits
        toxic_score = 0.5 * toxic_hits
        ui_score = 0.4 * ui_hits

        per_review_rage = base + diff_score + tech_score + toxic_score + ui_score

        rage_points_total += per_review_rage
        difficulty_points += diff_score
        tech_points += tech_score
        toxic_points += toxic_score
        ui_points += ui_score

    max_possible = total * 5.0
    factor = 100.0 / max_possible if max_possible > 0 else 0.0

    return {
        "review_rage": min(100.0, rage_points_total * factor),
        "difficulty_rage": min(100.0, difficulty_points * factor),
        "technical_rage": min(100.0, tech_points * factor),
        "social_toxicity_rage": min(100.0, toxic_points * factor),
        "ui_design_rage": min(100.0, ui_points * factor),
    }


def score_achievements_for_game(achievements: List[Dict]) -> Dict[str, Optional[float]]:
    """
    achievements: list of dicts like:
      {"api_name": str, "display_name": str, "percent": float}
    """
    if not achievements:
        return {
            "achievement_rage": 0.0,
            "max_achievement_drop": None,
            "max_drop_from": None,
            "max_drop_to": None,
            "max_drop_achievement": None,
        }

    ach_sorted = sorted(achievements, key=lambda a: a["percent"], reverse=True)

    max_drop = 0.0
    drop_from = None
    drop_to = None
    drop_ach_name = None

    for prev, cur in zip(ach_sorted, ach_sorted[1:]):
        drop = prev["percent"] - cur["percent"]
        if drop > max_drop:
            max_drop = drop
            drop_from = prev["percent"]
            drop_to = cur["percent"]
            drop_ach_name = cur.get("display_name") or cur["api_name"]

    achievement_rage = min(100.0, max_drop * (100.0 / 70.0))

    return {
        "achievement_rage": achievement_rage,
        "max_achievement_drop": max_drop,
        "max_drop_from": drop_from,
        "max_drop_to": drop_to,
        "max_drop_achievement": drop_ach_name,
    }


def combine_rage_scores(
    review_scores: Dict[str, float], ach_scores: Dict[str, Optional[float]]
) -> Dict[str, Optional[float]]:
    difficulty = min(
        100.0,
        review_scores["difficulty_rage"] * 0.7
        + (ach_scores["achievement_rage"] or 0.0) * 0.3,
    )
    technical = review_scores["technical_rage"]
    toxic = review_scores["social_toxicity_rage"]
    ui_design = review_scores["ui_design_rage"]

    rage_score = (
        0.4 * review_scores["review_rage"]
        + 0.3 * difficulty
        + 0.15 * technical
        + 0.1 * toxic
        + 0.05 * ui_design
    )

    return {
        "rage_score": min(100.0, rage_score),
        "difficulty_rage": difficulty,
        "technical_rage": technical,
        "social_toxicity_rage": toxic,
        "ui_design_rage": ui_design,
        "max_achievement_drop": ach_scores["max_achievement_drop"],
        "max_drop_from": ach_scores["max_drop_from"],
        "max_drop_to": ach_scores["max_drop_to"],
        "max_drop_achievement": ach_scores["max_drop_achievement"],
    }
