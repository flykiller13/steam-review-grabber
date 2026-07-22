# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-script Python job that polls the Steam store's review API for a game and posts new reviews to a Discord channel via webhook. It is run periodically by Jenkins (see `Jenkinsfile`, cron every ~6 hours on a Windows agent).

## Running

```
pip install requests
python steam_reviews.py <appid>
```

- The app ID comes from argv[1], falling back to the `STEAM_APPID` env var.
- `DISCORD_WEBHOOK_URL` env var is required (in Jenkins it comes from the `discord-reviews-webhook` credential).

There are no tests or linters configured.

## How it works

- `steam_reviews.py` fetches up to 2 pages (200 reviews) of recent reviews from `https://store.steampowered.com/appreviews/<appid>` using cursor pagination.
- Dedup state is kept in `seen_<APPID>.json` (a JSON list of recommendation IDs) in `STEAM_REVIEWS_STATE_DIR` (created if missing; defaults to the current working directory). On first run (no seen-file), it seeds the file silently without posting, to avoid spamming old reviews.
- New reviews are posted oldest-first as Discord embeds (green/red by verdict).

## Gotchas

- One seen-file per app ID; to track more games, add more `bat 'python steam_reviews.py <appid>'` lines in the Jenkinsfile.
