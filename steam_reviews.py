#!/usr/bin/env python3
import json, os, sys, requests
from pathlib import Path

# Each arg is "appid=Game Name" (or a bare appid, then the id doubles as the name),
# optionally with a per-game destination: "appid=Game Name=<webhook url>" posts to
# that webhook's channel, "appid=Game Name=<thread id>" posts to that thread of the
# default webhook's channel. Without a destination, the default webhook is used.
RAW_ARGS = sys.argv[1:] or os.environ["STEAM_APPID"].split(",")
DEFAULT_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL")
STATE_DIR = Path(os.environ.get("STEAM_REVIEWS_STATE_DIR", "."))

def parse_game(arg):
    parts = arg.split("=")
    # Only a trailing webhook URL or all-digit thread ID counts as a destination,
    # so game names containing "=" still parse as before.
    target = None
    if len(parts) > 2 and (parts[-1].startswith("http") or parts[-1].isdigit()):
        target = parts.pop()
    return parts[0], "=".join(parts[1:]) or parts[0], target

GAMES = [parse_game(a) for a in RAW_ARGS]

def webhook_for(target):
    if target and target.startswith("http"):
        return target
    if not DEFAULT_WEBHOOK:
        raise RuntimeError("DISCORD_WEBHOOK_URL is not set and no per-game webhook given")
    if target:  # thread ID within the default webhook's channel
        sep = "&" if "?" in DEFAULT_WEBHOOK else "?"
        return f"{DEFAULT_WEBHOOK}{sep}thread_id={target}"
    return DEFAULT_WEBHOOK

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

def translate(text):
    r = requests.get(
        "https://translate.googleapis.com/translate_a/single",
        params={"client": "gtx", "sl": "auto", "tl": "en", "dt": "t", "q": text},
        timeout=15,
    )
    r.raise_for_status()
    return "".join(chunk[0] for chunk in r.json()[0])

def process_game(appid, name, webhook):
    seen_file = STATE_DIR / f"seen_{appid}.json"
    seen = set(json.loads(seen_file.read_text())) if seen_file.exists() else set()
    first_run = not seen_file.exists()

    new = [rv for rv in fetch_recent(appid) if rv["recommendationid"] not in seen]

    for rv in reversed(new):  # oldest first
        seen.add(rv["recommendationid"])
        if first_run:
            continue  # seed the seen-file silently, don't spam 200 old reviews
        verdict = "👍 Recommended" if rv["voted_up"] else "👎 Not Recommended"
        text = rv["review"][:1000] + ("…" if len(rv["review"]) > 1000 else "")
        if rv.get("language") != "english":
            try:  # best-effort: post the original untranslated on any failure
                text += f"\n\n🌐 {translate(text)[:1000]}"
            except Exception as e:
                print(f"{name} ({appid}): translation failed for "
                      f"{rv['recommendationid']}: {e}", file=sys.stderr)
        payload = {
            "embeds": [{
                "title": f"{name}: {verdict} — {rv['author']['playtime_forever'] // 60}h played",
                "description": text,
                "color": 0x57F287 if rv["voted_up"] else 0xED4245,
                "footer": {"text": f"{name} (app {appid}) • helpful votes: {rv['votes_up']}"},
            }]
        }
        resp = requests.post(webhook, json=payload, timeout=15)
        resp.raise_for_status()

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    seen_file.write_text(json.dumps(sorted(seen)))
    if first_run:
        print(f"{name} ({appid}): first run, seeded {len(new)} review(s), nothing posted")
    else:
        print(f"{name} ({appid}): {len(new)} new review(s) posted")

def main():
    failed = []
    for appid, name, target in GAMES:
        try:
            process_game(appid, name, webhook_for(target))
        except Exception as e:
            print(f"{name} ({appid}): FAILED: {e}", file=sys.stderr)
            failed.append(name)
    if failed:
        sys.exit(f"failed for: {', '.join(failed)}")

if __name__ == "__main__":
    main()
