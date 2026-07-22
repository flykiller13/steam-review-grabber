#!/usr/bin/env python3
import json, os, sys, requests
from pathlib import Path

APPID = sys.argv[1] if len(sys.argv) > 1 else os.environ["STEAM_APPID"]
WEBHOOK = os.environ["DISCORD_WEBHOOK_URL"]
SEEN_FILE = Path(f"seen_{APPID}.json")

def fetch_recent(appid, pages=2):
    reviews, cursor = [], "*"
    for _ in range(pages):
        r = requests.get(
            f"https://store.steampowered.com/appreviews/{appid}",
            params={"json": 1, "filter": "recent", "num_per_page": 100,
                    "language": "all", "purchase_type": "all", "cursor": cursor},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        reviews += data.get("reviews", [])
        cursor = data.get("cursor")
        if not cursor or not data.get("reviews"):
            break
    return reviews

def main():
    seen = set(json.loads(SEEN_FILE.read_text())) if SEEN_FILE.exists() else set()
    first_run = not SEEN_FILE.exists()

    new = [rv for rv in fetch_recent(APPID) if rv["recommendationid"] not in seen]

    for rv in reversed(new):  # oldest first
        seen.add(rv["recommendationid"])
        if first_run:
            continue  # seed the seen-file silently, don't spam 200 old reviews
        verdict = "👍 Recommended" if rv["voted_up"] else "👎 Not Recommended"
        text = rv["review"][:1000] + ("…" if len(rv["review"]) > 1000 else "")
        payload = {
            "embeds": [{
                "title": f"{verdict} — {rv['author']['playtime_forever'] // 60}h played",
                "description": text,
                "color": 0x57F287 if rv["voted_up"] else 0xED4245,
                "footer": {"text": f"App {APPID} • helpful votes: {rv['votes_up']}"},
            }]
        }
        resp = requests.post(WEBHOOK, json=payload, timeout=15)
        resp.raise_for_status()

    SEEN_FILE.write_text(json.dumps(sorted(seen)))
    print(f"{len(new)} new review(s)")

if __name__ == "__main__":
    main()