from __future__ import annotations

from pathlib import Path


def ensure_generated_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_generated_bot(base_dir: Path, file_name: str, content: str) -> Path:
    if Path(file_name).name != file_name or "/" in file_name or "\\" in file_name:
        raise ValueError("Refusing to write non-basename generated bot filename.")
    root = ensure_generated_dir(base_dir).resolve()
    target = (root / file_name).resolve()
    if root not in target.parents or target.suffix != ".py":
        raise ValueError("Refusing to write outside generated bot directory.")
    target.write_text(content, encoding="utf-8")
    return target
