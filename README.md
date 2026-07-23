# Steam Reviews → Discord

Polls the Steam store review API for one or more games and posts new reviews to Discord as embeds (green for positive, red for negative). Each game can post to its own channel or thread. Reviews not in English are translated. Designed to run periodically as a Jenkins job.

## How it works

- Fetches the most recent reviews for each configured game.
- Remembers which reviews it has already posted in `seen_<appid>.json` files, so each review is only posted once.
- On the first run for a game it just records the existing reviews without posting, to avoid spamming old reviews into the channel.

## Jenkins setup

1. **Create a Discord webhook** for the target channel (Channel settings → Integrations → Webhooks) and copy its URL.
2. **Add two credentials** in Jenkins (Manage Jenkins → Credentials), both of kind *Secret text*:

   | ID | Value |
   |----|-------|
   | `discord-reviews-webhook` | The Discord webhook URL (default destination) |
   | `steam-games` | Comma-separated `appid=Game Name` pairs, e.g. `123456=My Game,234567=Other Game` |

   The app ID is the number in a game's Steam store URL (`store.steampowered.com/app/<appid>/...`).

### Per-game channels or threads

Each `steam-games` entry accepts an optional third field that routes that game's reviews to its own destination:

- `appid=Game Name=<webhook url>` — posts to that webhook's channel (create a webhook per channel).
- `appid=Game Name=<thread id>` — posts to that thread inside the default webhook's channel (right-click the thread → Copy Thread ID, requires Developer Mode). The thread must already exist and not be archived.
- `appid=Game Name` — posts to the default webhook, as before. The three forms can be mixed.

Example: `123456=My Game=https://discord.com/api/webhooks/111/aaa,234567=Other Game=9876543210987654321`

A trailing field only counts as a destination if it's a URL or all digits, so game names containing `=` still work. `discord-reviews-webhook` is only required if at least one entry lacks its own webhook URL.
3. **Create a Pipeline job** pointing at this repository (Pipeline script from SCM). The `Jenkinsfile` runs the script every ~6 hours via cron.
4. The agent needs **Python 3** with `pip` on its `PATH`. Dependencies (`requests`) are installed by the job itself.
5. Optionally adjust `STEAM_REVIEWS_STATE_DIR` in the `Jenkinsfile` — the directory where the seen-review state files are kept (default `C:\Jenkins\data\steam_reviews`). It must persist between builds; don't point it inside the workspace.

To add or remove a game later, just edit the `steam-games` credential — no code changes needed.

## Running locally

```
pip install requests
set DISCORD_WEBHOOK_URL=<webhook url>
python steam_reviews.py "123456=My Game" "234567=Other Game"
```

Game args can also come from a `STEAM_APPID` env var (same comma-separated format) instead of the command line, and take the same optional per-game destination third field described above. State files are written to the current directory unless `STEAM_REVIEWS_STATE_DIR` is set.
