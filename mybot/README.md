# MyBot

Server-side Telegram AI control bot for coding help and child-bot generation.

## Setup

```bash
cd /workspace/mybot
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill `.env` with your real bot token and admin ID.

## Local AI

Set `USE_LOCAL_AI=true` and place the GGUF model at `MODEL_PATH`.

## Remote AI

Set `USE_LOCAL_AI=false` and point `REMOTE_AI_URL` to your inference endpoint.
The bot sends `prompt`, `messages`, `max_tokens`, and `temperature` in JSON.

## Run

```bash
cd /workspace/mybot && pwd
python bot.py
```

The startup guard must print a path ending in `/mybot`.

## Safety

- Only admin IDs can use the bot.
- `/lock` blocks all commands except `/unlock`.
- Any disk write requires the `1 ` prefix.
- Child bots are written only to `/workspace/mybot/generated`.
