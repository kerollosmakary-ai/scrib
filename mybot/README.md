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

## Safety

- Only admin IDs can use the bot.
- `/lock` blocks all commands except `/unlock`.
- Any disk write requires the `1 ` prefix.
- Child bots are written only to `/home/ubuntu/scrib/mybot/generated`.

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
   REMOTE_AI_URL=https://your-inference-endpoint
   REMOTE_AI_TOKEN=
   GENERATED_DIR=/home/ubuntu/scrib/mybot/generated
   EXPECTED_DIR_NAME=mybot
   ```

4. Ensure generated dir exists and is writable:

   ```bash
   mkdir -p /home/ubuntu/scrib/mybot/generated
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
