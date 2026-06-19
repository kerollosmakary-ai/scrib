from __future__ import annotations

import re
from dataclasses import dataclass

from ai_engine import AIEngine
from prompts import CHILD_BOT_PROMPT


@dataclass
class GeneratedBotPreview:
    file_name: str
    source_code: str


def build_generated_bot(request_text: str, ai_engine: AIEngine) -> GeneratedBotPreview:
    file_name = f"{derive_bot_name(request_text)}.py"
    prompt = CHILD_BOT_PROMPT.format(input=request_text)
    source = extract_python(ai_engine.ai_run(prompt))
    return GeneratedBotPreview(file_name=file_name, source_code=source)


def derive_bot_name(request_text: str) -> str:
    lowered = request_text.lower()
    match = re.search(r"(?:called|named)\s+([a-z0-9_\- ]+)", lowered)
    candidate = match.group(1) if match else lowered.replace("create bot", "", 1)
    slug = re.sub(r"[^a-z0-9]+", "_", candidate).strip("_")
    return slug[:40] or "generated_bot"


def extract_python(reply: str) -> str:
    match = re.search(r"```python\s*(.*?)```", reply, flags=re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip() + "\n"
    generic = re.search(r"```\s*(.*?)```", reply, flags=re.DOTALL)
    if generic:
        return generic.group(1).strip() + "\n"
    return reply.strip() + "\n"
