# Scrib AI Telegram Renovation Plan

## Summary

Add a new Python-based Telegram control bot under `/workspace/mybot` without changing the existing Android `Scrib` app behavior. The bot provides AI-assisted code analysis/generation features, enforces a strict `1 ` safety prefix before any disk-changing action, supports either a local GGUF model or a remote HTTP inference endpoint, and can generate additional single-file Telegram bots from natural-language requests for the admin only.

## Current State Analysis

- The current repository is an Android/Kotlin app only:
  - App module: `/workspace/app`
  - Main entrypoints: `/workspace/app/src/main/kotlin/dev/thaulow/scrib/MainActivity.kt`, `/workspace/app/src/main/kotlin/dev/thaulow/scrib/MainViewModel.kt`
  - CI/release workflows only build/test Android: `/workspace/.github/workflows/ci.yml`, `/workspace/.github/workflows/release.yml`
- There is no existing `mybot` directory, no `bot.py`, no Python dependency file, and no Telegram/Python code anywhere in the repo.
- Root `.gitignore` currently ignores Android/IDE artifacts and keystores only; it does not ignore Python caches, virtualenvs, `.env` files, generated bot output, or local AI model files.
- The requested implementation therefore cannot be an in-place extension of an existing Python bot in this workspace; it must be introduced as a new subtree.

## Assumptions & Decisions

- Target is a new Python Telegram bot at `/workspace/mybot`.
- Existing Android `Scrib` code remains untouched unless later explicitly requested.
- Only the admin can operate sensitive AI/coding and bot-generation features.
- Generated child bots are single Python files written to disk only when the admin message starts with `1 `.
- Remote AI mode is a real HTTP API integration to a configurable `server:port`, not a placeholder.
- Secrets such as Telegram bot tokens and admin IDs must be loaded from environment/config files that are gitignored, not hardcoded into tracked source.
- “Cloud server telegram to telegram” is interpreted as the main bot and generated child bots both operating as Telegram bots and using server-side execution.
- Safety procedures remain global:
  - read-only replies are allowed without `1 `
  - any write/create/save action requires the exact `1 ` prefix
  - task lock can block all non-unlock operations
  - only minimal, targeted file output is produced for fixes when requested later

## Proposed Changes

### 1. New Python bot workspace

- Add `/workspace/mybot/bot.py`
  - Main Telegram bot entrypoint.
  - Keeps startup guard that confirms runtime location and logs/returns a folder check result before normal operation.
  - Loads config, initializes AI backend, registers handlers, and starts polling.
- Add `/workspace/mybot/config.py`
  - Centralizes environment-driven settings:
    - main Telegram bot token
    - admin user ID allowlist
    - local/remote AI switch
    - local model path
    - remote endpoint URL and optional auth header
    - output directories for generated bots
    - safety prefix and task-lock defaults
- Add `/workspace/mybot/requirements.txt`
  - Minimal Python dependency list for:
    - Telegram bot framework
    - `llama-cpp-python`
    - HTTP client for remote inference
    - optional env loader
- Add `/workspace/mybot/.env.example`
  - Documents required runtime variables without exposing real secrets.
- Add `/workspace/mybot/README.md`
  - Documents setup, model download, remote endpoint configuration, run commands, and safety semantics.

### 2. Internal bot modules for maintainability

- Add `/workspace/mybot/ai_engine.py`
  - Provides a single `ai_run()` interface.
  - Implements:
    - local GGUF execution via `llama_cpp.Llama`
    - remote HTTP inference via configurable endpoint
  - Normalizes prompt/response handling and clear error messages if the model or server is unavailable.
- Add `/workspace/mybot/safety.py`
  - Implements:
    - `is_allowed_change(text)`
    - `clean_input(text)`
    - admin validation helpers
    - task-lock state helpers
  - Keeps all write-gating logic in one place.
- Add `/workspace/mybot/prompts.py`
  - Stores prompt templates for:
    - error analysis
    - line-by-line explanation
    - full-code generation
    - folder restructuring
    - AIDE-like recovery
    - Termux/Trimix commands
    - child-bot generation from NLP
- Add `/workspace/mybot/bot_generator.py`
  - Builds a safe single-file child bot template from structured inputs inferred from the admin’s natural-language request.
  - Produces:
    - preview text when `1 ` is absent
    - actual file content/path when `1 ` is present
  - Sanitizes generated filenames and prevents path traversal.
- Add `/workspace/mybot/storage.py`
  - Handles controlled writes for generated child bots and optional metadata index files.
  - Ensures writes stay under a dedicated generated-bots directory.

### 3. Telegram command and message handling

- In `/workspace/mybot/bot.py`, implement focused handlers before catch-all:
  - `/start`, `/help`, `/status`
  - `/lock <task>` and `/unlock`
  - text commands beginning with `error` or `find bug`
  - text commands beginning with `explain`
  - text commands beginning with `write`, `build`, or `make`
  - text containing `restructure`
  - text containing `recover`, `rebuild`, or `decompile`
  - text containing `termux`, `trimix`, or `command`
  - text command for child-bot generation, e.g. `create bot ...`
- Keep an admin-only catch-all AI conversation handler after the specific routes.
- Apply task lock before any command that is not `/unlock`.
- For write-capable commands:
  - without `1 `: return preview/instructions only
  - with `1 `: allow file creation only inside the managed output directory

### 4. Child-bot generation flow

- Add `/workspace/mybot/generated/` as the managed output directory for generated bots.
- Support a natural-language request such as “create a Telegram bot that ...”.
- Planned flow:
  - parse request into intent + bot name + behavior
  - ask AI to produce a compact single-file Telegram bot implementation
  - validate/sanitize output boundaries
  - show preview if no `1 `
  - write `<sanitized_name>.py` if prefixed with `1 `
- Generated bots should also follow the same broad principles where practical:
  - env-based token loading
  - no hardcoded secrets
  - short focused handlers
  - simple run instructions

### 5. Remote AI HTTP integration

- In `/workspace/mybot/ai_engine.py`, support a configurable HTTP request contract such as:
  - POST to configured endpoint
  - send prompt/messages payload plus generation settings
  - parse a text response from a documented response shape
- Keep the remote client isolated so later the endpoint contract can be swapped without changing handler logic.
- Return actionable failures to Telegram if:
  - endpoint is unreachable
  - auth is invalid
  - response shape is malformed

### 6. Repo hygiene updates

- Update `/workspace/.gitignore`
  - Ignore:
    - Python bytecode/cache
    - virtualenv directories
    - `.env` files
    - local GGUF model files under `/workspace/mybot`
    - generated child bots and metadata if they should remain local-only
- Update `/workspace/README.md`
  - Add a short section noting the repo now also contains a server-side Telegram AI bot under `/workspace/mybot`, separate from the Android app.
- Optionally update `/workspace/.github/workflows/ci.yml`
  - Add a lightweight Python syntax/import smoke step for `/workspace/mybot` without disturbing the Android build.
  - If this is judged too invasive for the first pass, defer CI changes and document manual verification instead.

## File-by-File Execution Outline

- `/workspace/mybot/bot.py`
  - Create runtime bootstrap, admin gatekeeping, handler registration, polling.
- `/workspace/mybot/config.py`
  - Create settings loader and config validation.
- `/workspace/mybot/ai_engine.py`
  - Implement local GGUF and remote HTTP execution paths.
- `/workspace/mybot/safety.py`
  - Implement `1 ` prefix gate, task lock, and write permission checks.
- `/workspace/mybot/prompts.py`
  - Add reusable instruction templates for each supported AI capability.
- `/workspace/mybot/bot_generator.py`
  - Generate child bot source text and sanitize filenames.
- `/workspace/mybot/storage.py`
  - Implement bounded file writes and optional manifest tracking.
- `/workspace/mybot/requirements.txt`
  - Add Python runtime dependencies.
- `/workspace/mybot/.env.example`
  - Add documented sample configuration.
- `/workspace/mybot/README.md`
  - Add setup/run/usage instructions.
- `/workspace/.gitignore`
  - Add Python and secret/model ignores.
- `/workspace/README.md`
  - Add brief repository-structure note for the new bot subtree.
- `/workspace/.github/workflows/ci.yml` (optional in first pass)
  - Add minimal Python validation if desired.

## Edge Cases & Failure Modes

- Missing `mybot` directory on first run:
  - Implementation creates the subtree and required generated-bots directory.
- Bot launched from the wrong directory:
  - Startup prints/responds with the actual working directory and refuses normal execution until expected layout is confirmed.
- Missing Telegram token/admin ID:
  - Fail fast with a clear configuration error.
- Local model file missing while local mode is enabled:
  - Return a clear error with the expected model path.
- Remote server endpoint unavailable:
  - Reply with a bounded failure message instead of hanging.
- Non-admin user messages:
  - Deny access without exposing config/state.
- Task lock enabled:
  - Reject all operations except `/unlock`.
- Dangerous filename or prompt trying to escape output directory:
  - Sanitize name and constrain writes to `/workspace/mybot/generated`.
- AI output contains explanation mixed with code for child-bot generation:
  - Post-process or wrap generation prompt so disk writes only use the extracted Python body.

## Verification Steps

- Static verification
  - Confirm new files live under `/workspace/mybot` and do not interfere with `/workspace/app`.
  - Confirm `.gitignore` protects secrets, models, and Python artifacts.
- Local/runtime verification
  - Install Python deps from `/workspace/mybot/requirements.txt`.
  - Run the main bot with env vars set.
  - Verify startup folder check reports the expected `/workspace/mybot` path.
- Functional bot checks
  - Send admin messages for:
    - `explain ...`
    - `find bug ...`
    - `write ...`
    - `recover ...`
    - `termux ...`
    - `/lock ...` and `/unlock`
  - Confirm non-admin requests are rejected.
- Safety checks
  - Confirm write-capable prompts do not write files without `1 `.
  - Confirm `1 create bot ...` writes exactly one generated `.py` file to `/workspace/mybot/generated`.
  - Confirm malformed filenames cannot escape the generated directory.
- Remote AI checks
  - Verify configured HTTP endpoint is called in remote mode and failures are surfaced cleanly.
- Optional CI checks
  - If CI is updated, confirm Android build remains unaffected and Python smoke validation passes.

## Notes For Execution

- Do not hardcode real Telegram tokens or user secrets into tracked files.
- Preserve the user’s requested interaction style:
  - prefer additive edits over rewrites
  - keep inserted code blocks compact
  - for later correction requests, return only the wrong line plus the fix where possible
- Because this repo currently has no Python tooling, execution should proceed incrementally:
  1. scaffold `/workspace/mybot`
  2. implement config/safety/AI engine
  3. wire Telegram handlers
  4. add child-bot generation
  5. update docs/ignores
  6. run focused verification
