# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-script Python job that polls the Steam store's review API for a game and posts new reviews to a Discord channel via webhook. It is run periodically by Jenkins (see `Jenkinsfile`, cron every ~6 hours on a Windows agent).

## Running

```
pip install requests
python steam_reviews.py "<appid>=<Game Name>" ["<appid>=<Game Name>" ...]
```

- Each arg is an `appid=Game Name` pair (a bare appid also works; the id is then used as the display name), with an optional third field routing that game to its own destination: a full webhook URL (separate channel) or a numeric thread ID (thread in the default webhook's channel, sent via Discord's `?thread_id=` webhook parameter). The trailing field is only treated as a destination if it starts with `http` or is all digits, so names containing `=` still parse. With no args, it falls back to the `STEAM_APPID` env var (comma-separated).
- `DISCORD_WEBHOOK_URL` env var is the default destination (in Jenkins it comes from the `discord-reviews-webhook` credential); it's only required if at least one game doesn't specify its own webhook URL. The game name is shown in each embed.

There are no tests or linters configured.

## How it works

- `steam_reviews.py` fetches up to 2 pages (200 reviews) of recent reviews from `https://store.steampowered.com/appreviews/<appid>` using cursor pagination.
- Dedup state is kept in `seen_<APPID>.json` (a JSON list of recommendation IDs) in `STEAM_REVIEWS_STATE_DIR` (created if missing; defaults to the current working directory). On first run (no seen-file), it seeds the file silently without posting, to avoid spamming old reviews.
- New reviews are posted oldest-first as Discord embeds (green/red by verdict).

## Gotchas

- One seen-file per app ID. Games are processed independently: a failure for one game is logged and the rest still run; the script exits non-zero at the end if any game failed.
- The Jenkinsfile contains no game-specific data (this is a template repo). The game list comes from the `steam-games` Jenkins secret-text credential, exposed as `STEAM_APPID`: comma-separated `appid=Game Name` pairs, each optionally suffixed with `=<webhook url>` or `=<thread id>` for a per-game destination. To add a game or change where it posts, edit that credential in Jenkins — no repo change needed.
