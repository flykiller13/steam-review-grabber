# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-script Python job that polls the Steam store's review API for a game and posts new reviews to a Discord channel via webhook. It is run periodically by Jenkins (see `Jenkinsfile`, cron every ~6 hours on a Windows agent).

## Running

```
pip install requests
python steam_reviews.py [path/to/games.json]
```

- Config is a JSON list of game objects: `appid` (required), `name` (display name, defaults to the appid), `webhook` (per-game Discord webhook URL) and `thread_id` (thread within the target webhook's channel, sent via Discord's `?thread_id=` webhook parameter) are optional. Path comes from the first CLI arg, else the `STEAM_GAMES_FILE` env var, else `./games.json`. See the README for an example.
- `DISCORD_WEBHOOK_URL` env var is the default destination (in Jenkins it comes from the `discord-reviews-webhook` credential); it's only required if at least one game doesn't specify its own `webhook`. The game name is shown in each embed.

There are no tests or linters configured.

## How it works

- `steam_reviews.py` fetches up to 2 pages (200 reviews) of recent reviews from `https://store.steampowered.com/appreviews/<appid>` using cursor pagination.
- Dedup state is kept in `seen_<APPID>.json` (a JSON list of recommendation IDs) in `STEAM_REVIEWS_STATE_DIR` (created if missing; defaults to the current working directory). On first run (no seen-file), it seeds the file silently without posting, to avoid spamming old reviews.
- New reviews are posted oldest-first as Discord embeds (green/red by verdict).

## Gotchas

- One seen-file per app ID. Games are processed independently: a failure for one game is logged and the rest still run; the script exits non-zero at the end if any game failed.
- The Jenkinsfile contains no game-specific data (this is a template repo). `games.json` lives in the `steam-games-file` Jenkins secret-file credential, exposed as the `STEAM_GAMES_FILE` path. To add a game or change where it posts, re-upload that credential's file in Jenkins — no repo change needed.
- The config can contain webhook URLs and Jenkins does not mask secret-file *contents* in logs, so the script must never print anything from the config except app IDs and names (this is why the Discord post error avoids `raise_for_status`, whose message includes the URL).
