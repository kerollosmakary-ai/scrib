from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional at runtime
    load_dotenv = None


ROOT_DIR = Path(__file__).resolve().parent
GENERATED_DIR = ROOT_DIR / "generated"

if load_dotenv is not None:
    load_dotenv(ROOT_DIR / ".env")


def _parse_admin_ids(raw: str) -> set[int]:
    admin_ids: set[int] = set()
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        admin_ids.add(int(item))
    return admin_ids


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    telegram_token: str
    admin_ids: set[int]
    use_local_ai: bool
    model_path: Path
    max_tokens: int
    temperature: float
    safety_prefix: str
    remote_ai_url: str
    remote_ai_token: str
    generated_dir: Path
    expected_dir_name: str


def load_settings() -> Settings:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    admin_ids = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))
    return Settings(
        telegram_token=token,
        admin_ids=admin_ids,
        use_local_ai=_bool_env("USE_LOCAL_AI", True),
        model_path=Path(os.getenv("MODEL_PATH", ROOT_DIR / "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")).expanduser(),
        max_tokens=int(os.getenv("MAX_TOKENS", "768")),
        temperature=float(os.getenv("TEMPERATURE", "0.3")),
        safety_prefix=os.getenv("SAFETY_PREFIX", "1 "),
        remote_ai_url=os.getenv("REMOTE_AI_URL", "").strip(),
        remote_ai_token=os.getenv("REMOTE_AI_TOKEN", "").strip(),
        generated_dir=Path(os.getenv("GENERATED_DIR", GENERATED_DIR)).expanduser(),
        expected_dir_name=os.getenv("EXPECTED_DIR_NAME", "mybot").strip() or "mybot",
    )


def validate_settings(settings: Settings) -> None:
    missing: list[str] = []
    if not settings.telegram_token:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not settings.admin_ids:
        missing.append("ADMIN_IDS")
    if not settings.use_local_ai and not settings.remote_ai_url:
        missing.append("REMOTE_AI_URL")
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"Missing required configuration: {joined}")
    if ROOT_DIR.resolve() not in settings.generated_dir.resolve().parents:
        raise RuntimeError("GENERATED_DIR must resolve under the mybot workspace.")
