from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TaskLock:
    active: bool = False
    task: str = ""

    def lock(self, task: str) -> None:
        self.active = True
        self.task = task.strip() or "general"

    def unlock(self) -> None:
        self.active = False
        self.task = ""


def is_admin(user_id: int, admin_ids: set[int]) -> bool:
    return user_id in admin_ids


def is_allowed_change(text: str, safety_prefix: str) -> bool:
    return text.strip().startswith(safety_prefix)


def is_command(text: str) -> bool:
    return text.strip().startswith("/")


def clean_input(text: str, safety_prefix: str) -> str:
    stripped = text.strip()
    if stripped.startswith(safety_prefix):
        return stripped[len(safety_prefix):].strip()
    return stripped


def task_lock_message(task_lock: TaskLock) -> str:
    return f"LOCKED ON: {task_lock.task}\nSend /unlock first"
