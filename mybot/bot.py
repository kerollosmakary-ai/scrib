from __future__ import annotations

import os
import sys

import telebot

from ai_engine import AIEngine
from bot_generator import build_generated_bot
from config import load_settings, validate_settings
from prompts import (
    ERROR_ANALYSIS_PROMPT,
    EXPLAIN_CODE_PROMPT,
    RECOVERY_PROMPT,
    RESTRUCTURE_PROMPT,
    TERMUX_PROMPT,
    WRITE_CODE_PROMPT,
)
from safety import TaskLock, clean_input, is_admin, is_allowed_change, is_command, task_lock_message
from storage import write_generated_bot


EXPECTED_DIR_NAME = os.getenv("EXPECTED_DIR_NAME", "mybot").strip() or "mybot"


def ensure_expected_folder() -> str:
    cwd = os.getcwd()
    if os.path.basename(cwd) != EXPECTED_DIR_NAME:
        print(f"[FOLDER ERROR] Expected to run inside /{EXPECTED_DIR_NAME}, got: {cwd}")
        raise SystemExit(1)
    print(cwd)
    return cwd


ensure_expected_folder()
settings = load_settings()
validate_settings(settings)
ai_engine = AIEngine(settings)
task_lock = TaskLock()
bot = telebot.TeleBot(settings.telegram_token)


def ai_rules_prefix() -> str:
    return (
        "Rules forever:\n"
        "- confirm folder first\n"
        "- prefer add/put/replace over full rewrites\n"
        "- keep code blocks short\n"
        "- if fixing later, show wrong line and fix only\n\n"
    )


def guard_admin(message: telebot.types.Message) -> bool:
    if is_admin(message.from_user.id, settings.admin_ids):
        return True
    bot.send_message(message.chat.id, "Access denied")
    return False


def guard_lock(message: telebot.types.Message) -> bool:
    if not task_lock.active or message.text.strip() == "/unlock":
        return True
    bot.reply_to(message, task_lock_message(task_lock))
    return False


def prompt_reply(message: telebot.types.Message, template: str, suffix: str = "") -> None:
    if not guard_admin(message) or not guard_lock(message):
        return
    payload = template.format(input=clean_input(message.text, settings.safety_prefix))
    reply = ai_engine.ai_run(ai_rules_prefix() + payload)
    if suffix:
        reply = f"{reply}\n\n{suffix}"
    bot.reply_to(message, reply)


@bot.message_handler(commands=["start", "help"])
def cmd_help(message: telebot.types.Message) -> None:
    if not guard_admin(message):
        return
    text = (
        "AI control bot ready.\n\n"
        "Use:\n"
        "- explain <code>\n"
        "- error <code>\n"
        "- write <request>\n"
        "- restructure <project>\n"
        "- recover <broken source>\n"
        "- termux <task>\n"
        "- create bot <request>\n"
        "- /lock <task>\n"
        "- /unlock\n"
        "- /status\n\n"
        f"Disk writes require prefix: {settings.safety_prefix!r}"
    )
    bot.reply_to(message, text)


@bot.message_handler(commands=["status"])
def cmd_status(message: telebot.types.Message) -> None:
    if not guard_admin(message) or not guard_lock(message):
        return
    mode = "local" if settings.use_local_ai else "remote"
    lock = task_lock.task if task_lock.active else "off"
    bot.reply_to(
        message,
        f"Status: OK\nMode: {mode}\nFolder: {os.getcwd()}\nGenerated: {settings.generated_dir}\nTask lock: {lock}",
    )


@bot.message_handler(commands=["lock", "unlock"])
def cmd_lock(message: telebot.types.Message) -> None:
    if not guard_admin(message) or not guard_lock(message):
        return
    if message.text.strip() == "/unlock":
        task_lock.unlock()
        bot.reply_to(message, "Task Lock OFF")
        return
    task = message.text.replace("/lock", "", 1).strip()
    task_lock.lock(task)
    bot.reply_to(message, f"Task Lock ON -> {task_lock.task}")


@bot.message_handler(func=lambda m: bool(m.text) and (m.text.lower().startswith("error") or m.text.lower().startswith("find bug")))
def cmd_errors(message: telebot.types.Message) -> None:
    prompt_reply(message, ERROR_ANALYSIS_PROMPT)


@bot.message_handler(func=lambda m: bool(m.text) and m.text.lower().startswith("explain"))
def cmd_explain(message: telebot.types.Message) -> None:
    prompt_reply(message, EXPLAIN_CODE_PROMPT)


@bot.message_handler(
    func=lambda m: bool(m.text)
    and (
        clean_input(m.text, settings.safety_prefix).lower().startswith("write")
        or clean_input(m.text, settings.safety_prefix).lower().startswith("build")
        or clean_input(m.text, settings.safety_prefix).lower().startswith("make")
    )
)
def cmd_write(message: telebot.types.Message) -> None:
    suffix = "INFO ONLY - no file path was provided, so this command returns code text only."
    prompt_reply(message, WRITE_CODE_PROMPT, suffix=suffix)


@bot.message_handler(func=lambda m: bool(m.text) and "restructure" in m.text.lower())
def cmd_restructure(message: telebot.types.Message) -> None:
    prompt_reply(message, RESTRUCTURE_PROMPT)


@bot.message_handler(
    func=lambda m: bool(m.text)
    and any(word in m.text.lower() for word in ("recover", "rebuild", "decompile"))
)
def cmd_recover(message: telebot.types.Message) -> None:
    prompt_reply(message, RECOVERY_PROMPT)


@bot.message_handler(
    func=lambda m: bool(m.text)
    and any(word in m.text.lower() for word in ("termux", "trimix", "command"))
)
def cmd_termux(message: telebot.types.Message) -> None:
    prompt_reply(message, TERMUX_PROMPT)


@bot.message_handler(
    func=lambda m: bool(m.text)
    and clean_input(m.text, settings.safety_prefix).lower().startswith("create bot")
)
def cmd_create_bot(message: telebot.types.Message) -> None:
    if not guard_admin(message) or not guard_lock(message):
        return
    request_text = clean_input(message.text, settings.safety_prefix)
    preview = build_generated_bot(request_text, ai_engine)
    if not is_allowed_change(message.text, settings.safety_prefix):
        bot.reply_to(
            message,
            f"PREVIEW ONLY - not saved.\nFile: {preview.file_name}\n\n{preview.source_code[:3500]}",
        )
        return
    saved_path = write_generated_bot(settings.generated_dir, preview.file_name, preview.source_code)
    bot.reply_to(message, f"Saved child bot to: {saved_path}")


@bot.message_handler(content_types=["text"], func=lambda m: bool(m.text) and not is_command(m.text))
def chat_all(message: telebot.types.Message) -> None:
    if not guard_admin(message) or not guard_lock(message):
        return
    bot.reply_to(message, ai_engine.ai_run(ai_rules_prefix() + clean_input(message.text, settings.safety_prefix)))


if __name__ == "__main__":
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except KeyboardInterrupt:
        sys.exit(0)
