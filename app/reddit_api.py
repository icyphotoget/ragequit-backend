from typing import List, Dict
import time
import requests

USER_AGENT = "RageQuit.io (local dev)"


def fetch_reddit_posts_for_game(
    game_name: str,
    max_pages: int = 3,
    posts_per_page: int = 25,
) -> List[Dict]:
    """
    Very simple Reddit scraper using the public search.json endpoint.
    This is not using the official API; it's enough for basic rage mining.
    """
    collected: List[Dict] = []
    after = None

    query = f"{game_name} rage OR unfair OR bullshit OR broken OR uninstall OR lag OR toxic OR cheater"

    for page in range(max_pages):
        params = {
            "q": query,
            "sort": "relevance",
            "limit": posts_per_page,
            "restrict_sr": "false",
            "t": "all",
        }
        if after:
            params["after"] = after

        headers = {"User-Agent": USER_AGENT}
        url = "https://www.reddit.com/search.json"

        try:
            resp = requests.get(url, params=params, headers=headers, timeout=20)
        except requests.RequestException as e:
            print(f"[ERROR] Reddit fetch failed for {game_name}: {e}")
            break

        if resp.status_code != 200:
            print(f"[ERROR] Reddit HTTP {resp.status_code} for {game_name}")
            break

        data = resp.json()
        children = data.get("data", {}).get("children", [])
        if not children:
            break

        for c in children:
            collected.append(c.get("data", {}))

        after = data.get("data", {}).get("after")
        print(f"[INFO] Reddit page {page+1} collected {len(collected)} posts for {game_name}")

        if not after:
            break

        time.sleep(1.5)

    return collected
