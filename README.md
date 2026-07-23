# Steam Reviews → Discord

Polls the Steam store review API for one or more games and posts new reviews to Discord as embeds (green for positive, red for negative). Each game can post to its own channel or thread. Reviews not in English are translated. Designed to run periodically as a Jenkins job.

## How it works

- Fetches the most recent reviews for each configured game.
- Remembers which reviews it has already posted in `seen_<appid>.json` files, so each review is only posted once.
- On the first run for a game it just records the existing reviews without posting, to avoid spamming old reviews into the channel.

## Jenkins setup

1. **Create a Discord webhook** for each target channel (Channel settings → Integrations → Webhooks) and copy its URL.
2. **Write a `games.json`** describing the games — a JSON list, one object per game:

   ```json
   [
     { "appid": 123456, "name": "My Game",
       "webhook": "https://discord.com/api/webhooks/111/aaa",
       "thread_id": "9876543210987654321" },
     { "appid": 234567, "name": "Other Game" }
   ]
   ```

   - `appid` (required) — the number in the game's Steam store URL (`store.steampowered.com/app/<appid>/...`).
   - `name` — display name shown in the embeds; defaults to the app ID.
   - `webhook` — that game's Discord webhook URL; defaults to the `discord-reviews-webhook` credential.
   - `thread_id` — posts into that thread of the target webhook's channel (right-click the thread → Copy Thread ID, requires Developer Mode). The thread must already exist and not be archived.
3. **Add two credentials** in Jenkins (Manage Jenkins → Credentials):

   | ID | Kind | Value |
   |----|------|-------|
   | `steam-games-file` | Secret file | The `games.json` file |
   | `discord-reviews-webhook` | Secret text | Default webhook URL — only needed if some game has no `webhook` of its own |

   The config lives only in the credential store; because webhook URLs inside it are not individually masked by Jenkins, the script never prints anything from it except app IDs and names.
4. **Create a Pipeline job** pointing at this repository (Pipeline script from SCM). The `Jenkinsfile` runs the script every ~6 hours via cron.
5. The agent needs **Python 3** with `pip` on its `PATH`. Dependencies (`requests`) are installed by the job itself.
6. Optionally adjust `STEAM_REVIEWS_STATE_DIR` in the `Jenkinsfile` — the directory where the seen-review state files are kept (default `C:\Jenkins\data\steam_reviews`). It must persist between builds; don't point it inside the workspace.

To add or remove a game later, update the `steam-games-file` credential (delete and re-upload the file) — no code changes needed.

## Running locally

```
pip install requests
python steam_reviews.py path\to\games.json
```

The config path can also come from the `STEAM_GAMES_FILE` env var; with neither, `games.json` in the current directory is used. Set `DISCORD_WEBHOOK_URL` if any game omits its `webhook`. State files are written to the current directory unless `STEAM_REVIEWS_STATE_DIR` is set.
