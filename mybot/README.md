# MyBot

Server-side Telegram AI control bot for coding help and child-bot generation.

## Setup

```bash
cd /home/ubuntu/scrib/mybot
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
cd /home/ubuntu/scrib/mybot && pwd
python bot.py
```

The startup guard must print a path ending in `/mybot`.

## Features

- Admin-only Telegram control bot on Ubuntu.
- Per-user isolated `note` and `task` state (stored by Telegram user ID).
- AI modes:
  - read-only analysis/debug (`analyze`, `debug`, `error`, `explain`)
  - write/edit mode (`edit <path> :: <instruction>`) with safety prefix
- Child bot generation with preview-first behavior.
- Audit logging for edit/generation actions.

## Safety

- Only admin IDs can use the bot.
- `/lock` blocks all commands except `/unlock`.
- Any disk write requires the `1 ` prefix.
- Child bots are written only to `/home/ubuntu/scrib/mybot/generated`.
- Code edits are constrained to `CODE_EDIT_ROOT`.
- Edit activity is logged to `EDIT_LOG_PATH`.

## Command quick reference

- `explain <code>`
- `error <code>` / `analyze <task>` / `debug <issue>`
- `write <request>`
- `edit <relative/path> :: <instruction>`
- `note` / `note <text>`
- `task list` / `task add <text>` / `task done <n>` / `task clear`
- `create bot <request>`
- `/lock <task>` / `/unlock` / `/status`

For write actions, prefix the message with `1 ` (example: `1 note update deploy checklist`).

## VPS deployment (systemd, remote AI)

All commands below assume installation at `/home/ubuntu/scrib/mybot`. If your path differs, replace it everywhere.

1. Clone and enter the bot folder:

   ```bash
   git clone https://github.com/<your-user>/scrib.git
   cd /home/ubuntu/scrib/mybot
   ```

2. Create env + install:

   ```bash
   python3 -m venv .venv
   . .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   ```

3. Configure `.env` for remote AI:

   ```env
   TELEGRAM_BOT_TOKEN=your_real_token
   ADMIN_IDS=123456789
   USE_LOCAL_AI=false
   MAX_TOKENS=768
   TEMPERATURE=0.3
   SAFETY_PREFIX=1 
   REMOTE_AI_URL=https://api.example.com/v1/chat/completions
   REMOTE_AI_TOKEN=
   GENERATED_DIR=/home/ubuntu/scrib/mybot/generated
   USER_DATA_DIR=/home/ubuntu/scrib/mybot/data
   CODE_EDIT_ROOT=/home/ubuntu/scrib/mybot
   EDIT_LOG_PATH=/home/ubuntu/scrib/mybot/data/edit_audit.log
   EXPECTED_DIR_NAME=mybot
   ```

4. Ensure writable dirs exist:

   ```bash
   mkdir -p /home/ubuntu/scrib/mybot/generated
   mkdir -p /home/ubuntu/scrib/mybot/data
   ```

5. Smoke test:

   ```bash
   cd /home/ubuntu/scrib/mybot
   . .venv/bin/activate
   python bot.py
   ```

   Startup must print a working path ending in `/mybot`.

6. Install service template:

   ```bash
   # edit deploy/mybot.service first if your user/path differs
   sudo cp deploy/mybot.service /etc/systemd/system/mybot.service
   sudo systemctl daemon-reload
   sudo systemctl enable mybot
   sudo systemctl start mybot
   sudo systemctl status mybot
   journalctl -u mybot -f
   ```

7. Update routine:

   ```bash
   sudo bash deploy/update-mybot.sh
   ```
