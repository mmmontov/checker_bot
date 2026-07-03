# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Telegram bot (aiogram v3) that polls u1host.com every 5 minutes for available "Облачный VPS" tariffs (Germany/Finland/Netherlands, under 1000₽/month, excluding the promo tariff) and notifies the admin user when new stock appears. Runs as a single Docker container.

## Commands

```bash
# Local run (outside Docker) — needs a .venv with requirements.txt installed
python bot.py

# Docker (the actual deployment method)
docker compose up -d --build      # build and start
docker compose logs -f            # tail logs
docker compose restart            # restart after code changes
docker compose down                # stop
```

There is no test suite, linter, or CI config in this repo. `.env` (BOT_TOKEN, ADMIN_ID) must exist before running — see `config.py` for the full list of env vars it reads.

## Architecture

**Plugin-style checkers, not a monolithic scraper.** The whole point of this design is that new sites can be added without touching the scheduler, notifier, or bot plumbing:

- `checkers/base.py` defines the contract: `Offer` (dataclass) and `BaseChecker` (abstract, one method: `async fetch_available() -> list[Offer]`).
- `checkers/u1host.py` is the only concrete checker today. Register new checkers by adding an instance to the `CHECKERS` list in `checkers/__init__.py` — that's the single edit point for adding a new site.
- `monitor.run_check()` iterates `CHECKERS` generically; it has no u1host-specific knowledge. A checker that raises is logged and skipped, so one broken site doesn't take down the others.

**Edge-triggered notifications, not polling spam.** `monitor.run_check()` diffs the current set of `Offer.key`s against the previous run's keys (persisted per-checker in `storage.py`'s JSON state file). It only sends a Telegram message for genuinely *new* keys, and suppresses notification entirely on the very first run ever (`is_first_run`) since there's no prior state to diff against — otherwise every checker's full current inventory would fire as "new" on first container start. The same `run_check()` function serves both the periodic loop (`manual=False`, proactive push) and the inline "check now" button (`manual=True`, returns a formatted status string instead of pushing).

**u1host.com has no API — it's scraped out of a JS bundle.** `checkers/u1host.py` fetches the index HTML to find the current `/main.js?v=<hash>` path (the hash changes on every site deploy, so it can't be hardcoded), then regex-extracts a hardcoded `tariffs` JS object out of that bundle. Key detail: `ITEM_RE` anchors each tariff object on its trailing `id: <number>` field rather than matching balanced `{...}`, because tariff descriptions contain nested template-literal braces (e.g. `` `2 ${t("GB")}` ``) that break naive brace-matching. Groups whose name contains `"3900"` are the promo tariff and are explicitly excluded.

**Data flow:** `bot.py` (entrypoint, starts `periodic_loop` as a background asyncio task + aiogram polling) → `handlers.py` (router: `/start`, inline-button callback) → `monitor.py` (orchestration) → `checkers/*` (fetch) + `storage.py` (diffing state) + `notifier.py` (HTML message formatting) → Telegram via the `Bot` object.

## Persistence

`data/state.json` (bind-mounted via `docker-compose.yml`) stores, per checker name, the list of currently-available offer keys from the last run. Deleting it resets edge-detection to "first run" — the next check won't fire notifications even if stock is available, it'll just seed the baseline.
