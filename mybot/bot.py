from __future__ import annotations

import os
import re
import sys

import telebot

from ai_engine import AIEngine
from bot_generator import build_generated_bot
from config import load_settings, validate_settings
from prompts import (
    ANALYZE_TASK_PROMPT,
    DEBUG_PROMPT,
    EDIT_FILE_PROMPT,
    ERROR_ANALYSIS_PROMPT,
    EXPLAIN_CODE_PROMPT,
    RECOVERY_PROMPT,
    RESTRUCTURE_PROMPT,
    TERMUX_PROMPT,
    WRITE_CODE_PROMPT,
)
from safety import TaskLock, clean_input, is_admin, is_allowed_change, task_lock_message
from storage import (
    add_user_task,
    clear_user_tasks,
    complete_user_task,
    get_user_note,
    list_user_tasks,
    log_edit_action,
    read_code_file,
    set_user_note,
    write_code_file,
    write_generated_bot,
)


EXPECTED_DIR_NAME = os.getenv("EXPECTED_DIR_NAME", "mybot").strip() or "mybot"
MAX_LOG_DETAILS_LENGTH = 180


def ensure_expected_folder() -> str:
    cwd = os.getcwd()
    if os.path.basename(cwd) != EXPECTED_DIR_NAME:
        print(f"[FOLDER ERROR] Expected to run inside /{EXPECTED_DIR_NAME}, got: {cwd}")
        raise SystemExit(1)
    print(cwd)
    return cwd


def _extract_code(text: str) -> str:
    fenced = re.search(r"```(?:[a-zA-Z0-9_+-]+)?\s*(.*?)```", text, flags=re.DOTALL)
    if fenced:
        return fenced.group(1).strip() + "\n"
    return text.strip() + "\n"


def _format_tasks(tasks: list[str]) -> str:
    if not tasks:
        return "No tasks saved for your user ID."
    rows = [f"{idx}. {task}" for idx, task in enumerate(tasks, start=1)]
    return "Your tasks:\n" + "\n".join(rows)


def _require_write_prefix(message: telebot.types.Message, action: str) -> bool:
    if is_allowed_change(message.text or "", settings.safety_prefix):
        return True
    bot.reply_to(message, f"PREVIEW ONLY - add prefix {settings.safety_prefix!r} to {action}.")
    return False


def _parse_edit_request(raw_text: str) -> tuple[str, str] | None:
    if "::" not in raw_text:
        return None
    path_part, instruction = raw_text.split("::", 1)
    relative_path = path_part.replace("edit", "", 1).strip()
    instruction = instruction.strip()
    if not relative_path or not instruction:
        return None
    return relative_path, instruction


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
        "- analyze <task>\n"
        "- debug <issue>\n"
        "- write <request>\n"
        "- edit <relative/path> :: <instruction>\n"
        "- restructure <project>\n"
        "- recover <broken source>\n"
        "- termux <task>\n"
        "- create bot <request>\n"
        "- note / note <text>\n"
        "- task list | task add <text> | task done <n> | task clear\n"
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
        (
            f"Status: OK\nMode: {mode}\nFolder: {os.getcwd()}\nGenerated: {settings.generated_dir}\n"
            f"User data: {settings.user_data_dir}\nCode edit root: {settings.code_edit_root}\nTask lock: {lock}"
        ),
    )


@bot.message_handler(commands=["lock", "unlock"])
def cmd_lock(message: telebot.types.Message) -> None:
    if not guard_admin(message):
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


@bot.message_handler(func=lambda m: bool(m.text) and m.text.lower().startswith("analyze"))
def cmd_analyze(message: telebot.types.Message) -> None:
    prompt_reply(message, ANALYZE_TASK_PROMPT)


@bot.message_handler(func=lambda m: bool(m.text) and m.text.lower().startswith("debug"))
def cmd_debug(message: telebot.types.Message) -> None:
    prompt_reply(message, DEBUG_PROMPT)


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


@bot.message_handler(func=lambda m: bool(m.text) and clean_input(m.text, settings.safety_prefix).lower().startswith("edit "))
def cmd_edit(message: telebot.types.Message) -> None:
    if not guard_admin(message) or not guard_lock(message):
        return
    clean = clean_input(message.text, settings.safety_prefix)
    parsed = _parse_edit_request(clean)
    if parsed is None:
        bot.reply_to(message, "Use: edit <relative/path> :: <instruction>")
        return
    relative_path, instruction = parsed
    try:
        target_path, current = read_code_file(settings.code_edit_root, relative_path)
    except (ValueError, OSError) as exc:
        bot.reply_to(message, f"Edit rejected: {exc}")
        return
    request = EDIT_FILE_PROMPT.format(path=relative_path, instruction=instruction, current_content=current)
    response = ai_engine.ai_run(ai_rules_prefix() + request)
    updated_content = _extract_code(response)
    if not _require_write_prefix(message, "apply code edits"):
        log_edit_action(
            settings.edit_log_path,
            user_id=message.from_user.id,
            mode="edit",
            target_path=relative_path,
            applied=False,
            details=f"preview instruction={instruction[:MAX_LOG_DETAILS_LENGTH]}",
        )
        bot.reply_to(
            message,
            f"PREVIEW ONLY - not saved.\nTarget: {target_path}\n\n{updated_content[:3500]}",
        )
        return
    try:
        saved_path = write_code_file(settings.code_edit_root, relative_path, updated_content)
    except (ValueError, OSError) as exc:
        bot.reply_to(message, f"Write failed: {exc}")
        return
    log_edit_action(
        settings.edit_log_path,
        user_id=message.from_user.id,
        mode="edit",
        target_path=relative_path,
        applied=True,
        details=f"applied instruction={instruction[:MAX_LOG_DETAILS_LENGTH]}",
    )
    bot.reply_to(message, f"Saved edit to: {saved_path}")


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


@bot.message_handler(func=lambda m: bool(m.text) and clean_input(m.text, settings.safety_prefix).lower().startswith("note"))
def cmd_note(message: telebot.types.Message) -> None:
    if not guard_admin(message) or not guard_lock(message):
        return
    clean = clean_input(message.text, settings.safety_prefix)
    parts = clean.split(maxsplit=1)
    user_id = message.from_user.id
    if len(parts) == 1:
        note = get_user_note(settings.user_data_dir, user_id)
        bot.reply_to(message, f"Your note:\n{note}" if note else "No note saved for your user ID.")
        return
    if not _require_write_prefix(message, "save note"):
        bot.reply_to(message, f"PREVIEW NOTE (not saved):\n{parts[1].strip()}")
        return
    set_user_note(settings.user_data_dir, user_id, parts[1])
    bot.reply_to(message, "Saved note for your user ID.")


@bot.message_handler(func=lambda m: bool(m.text) and clean_input(m.text, settings.safety_prefix).lower().startswith("task"))
def cmd_task(message: telebot.types.Message) -> None:
    if not guard_admin(message) or not guard_lock(message):
        return
    clean = clean_input(message.text, settings.safety_prefix)
    parts = clean.split(maxsplit=2)
    user_id = message.from_user.id
    if len(parts) == 1 or parts[1].lower() == "list":
        bot.reply_to(message, _format_tasks(list_user_tasks(settings.user_data_dir, user_id)))
        return
    action = parts[1].lower()
    if action == "add":
        if len(parts) < 3 or not parts[2].strip():
            bot.reply_to(message, "Use: task add <text>")
            return
        if not _require_write_prefix(message, "add task"):
            bot.reply_to(message, f"PREVIEW TASK (not saved): {parts[2].strip()}")
            return
        tasks = add_user_task(settings.user_data_dir, user_id, parts[2])
        bot.reply_to(message, _format_tasks(tasks))
        return
    if action == "done":
        if len(parts) < 3 or not parts[2].strip().isdigit():
            bot.reply_to(message, "Use: task done <index>")
            return
        if not _require_write_prefix(message, "complete task"):
            bot.reply_to(message, f"PREVIEW ONLY - would complete task #{parts[2].strip()}.")
            return
        try:
            removed, tasks = complete_user_task(settings.user_data_dir, user_id, int(parts[2].strip()))
        except IndexError:
            bot.reply_to(message, "Task index out of range.")
            return
        bot.reply_to(message, f"Completed: {removed}\n\n{_format_tasks(tasks)}")
        return
    if action == "clear":
        if not _require_write_prefix(message, "clear tasks"):
            bot.reply_to(message, "PREVIEW ONLY - would clear all your tasks.")
            return
        clear_user_tasks(settings.user_data_dir, user_id)
        bot.reply_to(message, "Cleared all your tasks.")
        return
    bot.reply_to(message, "Use: task list | task add <text> | task done <n> | task clear")


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
    log_edit_action(
        settings.edit_log_path,
        user_id=message.from_user.id,
        mode="child_bot",
        target_path=str(saved_path),
        applied=True,
        details=f"create bot request={request_text[:MAX_LOG_DETAILS_LENGTH]}",
    )
    bot.reply_to(message, f"Saved child bot to: {saved_path}")


@bot.message_handler(content_types=["text"])
def chat_all(message: telebot.types.Message) -> None:
    if not guard_admin(message) or not guard_lock(message):
        return
    bot.reply_to(message, ai_engine.ai_run(ai_rules_prefix() + clean_input(message.text, settings.safety_prefix)))


if __name__ == "__main__":
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except KeyboardInterrupt:
        sys.exit(0)
