#!/usr/bin/env python3
import difflib, json, os, sys, requests
from pathlib import Path

# Config is a JSON list of games: [{"appid": 123456, "name": "My Game",
# "webhook": "https://discord.com/api/webhooks/...", "thread_id": "987..."}, ...]
# Only "appid" is required. "webhook" defaults to DISCORD_WEBHOOK_URL; "thread_id"
# routes into a thread of the target webhook's channel. The config may contain
# webhook URLs, so nothing from it except appid/name is ever printed.
# --test [N]: repost the N (default 1) newest reviews per game without reading
# or writing the seen-files, for testing the posting pipeline repeatably.
_argv = sys.argv[1:]
TEST_N = None
if "--test" in _argv:
    _i = _argv.index("--test")
    _argv.pop(_i)
    TEST_N = int(_argv.pop(_i)) if _i < len(_argv) and _argv[_i].isdigit() else 1
CONFIG_PATH = Path(_argv[0] if _argv
                   else os.environ.get("STEAM_GAMES_FILE", "games.json"))
DEFAULT_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL")
STATE_DIR = Path(os.environ.get("STEAM_REVIEWS_STATE_DIR", "."))

GAMES = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))

def webhook_for(game):
    url = game.get("webhook") or DEFAULT_WEBHOOK
    if not url:
        raise RuntimeError("no per-game webhook and DISCORD_WEBHOOK_URL is not set")
    thread = game.get("thread_id")
    if thread:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}thread_id={thread}"
    return url

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

LANGUAGE_TAGS = {
    "arabic": ("ar", "🇸🇦"), "bulgarian": ("bg", "🇧🇬"), "schinese": ("zh-CN", "🇨🇳"),
    "tchinese": ("zh-TW", "🇹🇼"), "czech": ("cs", "🇨🇿"), "danish": ("da", "🇩🇰"),
    "dutch": ("nl", "🇳🇱"), "finnish": ("fi", "🇫🇮"), "french": ("fr", "🇫🇷"),
    "german": ("de", "🇩🇪"), "greek": ("el", "🇬🇷"), "hungarian": ("hu", "🇭🇺"),
    "italian": ("it", "🇮🇹"), "japanese": ("ja", "🇯🇵"), "koreana": ("ko", "🇰🇷"),
    "norwegian": ("no", "🇳🇴"), "polish": ("pl", "🇵🇱"), "portuguese": ("pt", "🇵🇹"),
    "brazilian": ("pt-BR", "🇧🇷"), "romanian": ("ro", "🇷🇴"), "russian": ("ru", "🇷🇺"),
    "spanish": ("es", "🇪🇸"), "latam": ("es-LA", "🌎"), "swedish": ("sv", "🇸🇪"),
    "thai": ("th", "🇹🇭"), "turkish": ("tr", "🇹🇷"), "ukrainian": ("uk", "🇺🇦"),
    "vietnamese": ("vi", "🇻🇳"),
}

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
    if TEST_N is not None:
        seen, first_run = set(), False
        new = fetch_recent(appid)[:TEST_N]
    else:
        seen = set(json.loads(seen_file.read_text())) if seen_file.exists() else set()
        first_run = not seen_file.exists()
        new = [rv for rv in fetch_recent(appid) if rv["recommendationid"] not in seen]

    for rv in reversed(new):  # oldest first
        seen.add(rv["recommendationid"])
        if first_run:
            continue  # seed the seen-file silently, don't spam 200 old reviews
        verdict = "👍 Recommended" if rv["voted_up"] else "👎 Not Recommended"
        text = rv["review"][:2000] + ("…" if len(rv["review"]) > 2000 else "")
        if rv.get("language") != "english":
            code, flag = LANGUAGE_TAGS.get(rv.get("language"), (rv.get("language"), "🌐"))
            try:  # best-effort: post the original untranslated on any failure
                translated = translate(text)[:2000]
                similarity = difflib.SequenceMatcher(
                    None, text.lower(), translated.lower()).ratio()
                if similarity < 0.95:
                    text += f"\n\n*{flag} translated from {code}:*\n{translated}"
            except Exception as e:
                print(f"{name} ({appid}): translation failed for "
                      f"{rv['recommendationid']}: {e}", file=sys.stderr)
        playtime_hours = rv["author"]["playtime_forever"] / 60
        playtime_str = f"{playtime_hours:.1f}" if playtime_hours < 10 else f"{playtime_hours:.0f}"
        payload = {
            "embeds": [{
                "title": f"{verdict} — {playtime_str}h played",
                "description": text,
                "color": 0x57F287 if rv["voted_up"] else 0xED4245,
                "footer": {"text": f"app {appid}"},
            }]
        }
        resp = requests.post(webhook, json=payload, timeout=15)
        if not resp.ok:  # no raise_for_status: its message would leak the webhook URL
            raise RuntimeError(f"Discord returned {resp.status_code}: {resp.text[:300]}")

    if TEST_N is not None:
        print(f"{name} ({appid}): TEST MODE: posted {len(new)} review(s), seen-file untouched")
        return
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    seen_file.write_text(json.dumps(sorted(seen)))
    if first_run:
        print(f"{name} ({appid}): first run, seeded {len(new)} review(s), nothing posted")
    else:
        print(f"{name} ({appid}): {len(new)} new review(s) posted")

def main():
    failed = []
    for game in GAMES:
        appid = str(game["appid"]).strip()
        name = game.get("name") or appid
        try:
            process_game(appid, name, webhook_for(game))
        except Exception as e:
            print(f"{name} ({appid}): FAILED: {e}", file=sys.stderr)
            failed.append(name)
    if failed:
        sys.exit(f"failed for: {', '.join(failed)}")

if __name__ == "__main__":
    main()
