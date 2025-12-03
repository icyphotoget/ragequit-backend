import time
from typing import List, Dict
import requests


USER_AGENT = "RageQuit.io (local dev)"


def fetch_steam_reviews(
    app_id: int,
    max_pages: int = 10,
    num_per_page: int = 100,
    filter_type: str = "all"  # "recent" or "all"
) -> List[Dict]:
    """
    Fetch Steam reviews for a game using the public store API.
    No API key required.
    """
    url = f"https://store.steampowered.com/appreviews/{app_id}"
    cursor = "*"
    collected: List[Dict] = []

    headers = {"User-Agent": USER_AGENT}

    for page in range(max_pages):
        params = {
            "json": 1,
            "filter": filter_type,   # "recent" or "all"
            "language": "all",
            "purchase_type": "all",
            "num_per_page": num_per_page,
            "cursor": cursor,
        }

        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15)
        except requests.RequestException as e:
            print(f"[ERROR] Failed to fetch reviews for app {app_id}: {e}")
            break

        if resp.status_code != 200:
            print(f"[ERROR] Reviews HTTP {resp.status_code} for app {app_id}")
            break

        data = resp.json()
        if data.get("success") != 1:
            print(f"[WARN] Reviews response not successful for app {app_id}: {data.get('success')}")
            break

        reviews = data.get("reviews", [])
        if not reviews:
            break

        collected.extend(reviews)
        cursor = data.get("cursor")
        if not cursor:
            break

        print(f"[INFO] Page {page+1}: total {len(collected)} reviews for app {app_id}")
        time.sleep(1.2)

    print(f"[INFO] Collected {len(collected)} reviews for app {app_id}")
    return collected


def fetch_global_achievements(app_id: int) -> List[Dict]:
    """
    Fetch global achievement percentages from the Steam Web API.
    This endpoint does NOT require an API key.
    """
    url = "https://api.steampowered.com/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v0002/"
    params = {
        "gameid": app_id,
        "format": "json",
    }

    headers = {"User-Agent": USER_AGENT}

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
    except requests.RequestException as e:
        print(f"[ERROR] Failed to fetch achievements for app {app_id}: {e}")
        return []

    if resp.status_code != 200:
        print(f"[ERROR] Achievements HTTP {resp.status_code} for app {app_id}")
        return []

    data = resp.json()
    ach_root = data.get("achievementpercentages", {})
    achievements = ach_root.get("achievements", []) or []

    print(f"[INFO] Collected {len(achievements)} achievements for app {app_id}")
    return achievements
