from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_generated_dir(path: Path) -> Path:
    return ensure_dir(path)


def write_generated_bot(base_dir: Path, file_name: str, content: str) -> Path:
    root = ensure_generated_dir(base_dir).resolve()
    target = (root / file_name).resolve()
    if root not in target.parents or target.suffix != ".py":
        raise ValueError("Refusing to write outside generated bot directory.")
    target.write_text(content, encoding="utf-8")
    return target


def _user_state_file(base_dir: Path, user_id: int) -> Path:
    return ensure_dir(base_dir / "users") / f"{user_id}.json"


def _default_state() -> dict[str, object]:
    return {"note": "", "tasks": []}


def load_user_state(base_dir: Path, user_id: int) -> dict[str, object]:
    state_file = _user_state_file(base_dir, user_id)
    if not state_file.exists():
        return _default_state()
    try:
        loaded = json.loads(state_file.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return _default_state()
    note = loaded.get("note")
    tasks = loaded.get("tasks")
    safe_note = note if isinstance(note, str) else ""
    safe_tasks = [task for task in tasks if isinstance(task, str)] if isinstance(tasks, list) else []
    return {"note": safe_note, "tasks": safe_tasks}


def save_user_state(base_dir: Path, user_id: int, state: dict[str, object]) -> None:
    state_file = _user_state_file(base_dir, user_id)
    payload = {
        "note": state.get("note", ""),
        "tasks": state.get("tasks", []),
    }
    tmp = state_file.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(state_file)


def get_user_note(base_dir: Path, user_id: int) -> str:
    state = load_user_state(base_dir, user_id)
    note = state.get("note")
    return note if isinstance(note, str) else ""


def set_user_note(base_dir: Path, user_id: int, note: str) -> None:
    state = load_user_state(base_dir, user_id)
    state["note"] = note.strip()
    save_user_state(base_dir, user_id, state)


def list_user_tasks(base_dir: Path, user_id: int) -> list[str]:
    state = load_user_state(base_dir, user_id)
    tasks = state.get("tasks")
    return [task for task in tasks if isinstance(task, str)] if isinstance(tasks, list) else []


def add_user_task(base_dir: Path, user_id: int, task: str) -> list[str]:
    state = load_user_state(base_dir, user_id)
    tasks_raw = state.get("tasks")
    tasks = [item for item in tasks_raw if isinstance(item, str)] if isinstance(tasks_raw, list) else []
    tasks.append(task.strip())
    state["tasks"] = tasks
    save_user_state(base_dir, user_id, state)
    return tasks


def complete_user_task(base_dir: Path, user_id: int, index_1based: int) -> tuple[str, list[str]]:
    state = load_user_state(base_dir, user_id)
    tasks_raw = state.get("tasks")
    tasks = [item for item in tasks_raw if isinstance(item, str)] if isinstance(tasks_raw, list) else []
    if index_1based < 1 or index_1based > len(tasks):
        raise IndexError("Task index out of range")
    removed = tasks.pop(index_1based - 1)
    state["tasks"] = tasks
    save_user_state(base_dir, user_id, state)
    return removed, tasks


def clear_user_tasks(base_dir: Path, user_id: int) -> None:
    state = load_user_state(base_dir, user_id)
    state["tasks"] = []
    save_user_state(base_dir, user_id, state)


def _safe_target(root: Path, relative_path: str) -> Path:
    rel = Path(relative_path)
    if rel.is_absolute():
        raise ValueError("Path must be relative to CODE_EDIT_ROOT")
    if any(part in {".", ".."} for part in rel.parts):
        raise ValueError("Invalid path")
    target = (root / rel).resolve()
    if root != target and root not in target.parents:
        raise ValueError("Refusing path outside CODE_EDIT_ROOT")
    return target


def read_code_file(code_edit_root: Path, relative_path: str) -> tuple[Path, str]:
    root = code_edit_root.resolve()
    target = _safe_target(root, relative_path)
    if not target.exists():
        return target, ""
    return target, target.read_text(encoding="utf-8")


def write_code_file(code_edit_root: Path, relative_path: str, content: str) -> Path:
    root = ensure_dir(code_edit_root).resolve()
    target = _safe_target(root, relative_path)
    ensure_dir(target.parent)
    target.write_text(content, encoding="utf-8")
    return target


def log_edit_action(
    log_path: Path,
    *,
    user_id: int,
    mode: str,
    target_path: str,
    applied: bool,
    details: str,
) -> None:
    ensure_dir(log_path.parent)
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "mode": mode,
        "target_path": target_path,
        "applied": applied,
        "details": details,
    }
    with log_path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(event, ensure_ascii=False) + "\n")
