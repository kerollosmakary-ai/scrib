from __future__ import annotations

from pathlib import Path

import requests

from config import Settings

try:
    from llama_cpp import Llama
except ImportError:  # pragma: no cover - optional at runtime
    Llama = None


class AIEngine:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._llm = None

    def ai_run(self, prompt: str) -> str:
        if self.settings.use_local_ai:
            return self._run_local(prompt)
        return self._run_remote(prompt)

    def _run_local(self, prompt: str) -> str:
        model_path = Path(self.settings.model_path)
        if not model_path.exists():
            return f"[LOCAL AI ERROR] Missing model file at: {model_path}"
        if Llama is None:
            return "[LOCAL AI ERROR] `llama-cpp-python` is not installed."
        if self._llm is None:
            self._llm = Llama(
                model_path=str(model_path),
                n_ctx=2048,
                n_threads=4,
                verbose=False,
            )
        out = self._llm.create_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.settings.max_tokens,
            temperature=self.settings.temperature,
        )
        return out["choices"][0]["message"]["content"].strip()

    def _run_remote(self, prompt: str) -> str:
        headers = {"Content-Type": "application/json"}
        if self.settings.remote_ai_token:
            headers["Authorization"] = f"Bearer {self.settings.remote_ai_token}"
        payload = {
            "prompt": prompt,
            "max_tokens": self.settings.max_tokens,
            "temperature": self.settings.temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        try:
            response = requests.post(
                self.settings.remote_ai_url,
                json=payload,
                headers=headers,
                timeout=120,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            return f"[REMOTE AI ERROR] {exc}"
        try:
            data = response.json()
        except ValueError:
            text = response.text.strip()
            return text or "[REMOTE AI ERROR] Empty non-JSON response."
        parsed = _extract_text(data)
        return parsed or "[REMOTE AI ERROR] Could not parse response payload."


def _extract_text(data: object) -> str:
    if isinstance(data, str):
        return data.strip()
    if not isinstance(data, dict):
        return ""
    for key in ("text", "response", "content", "output"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            message = first.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()
            text = first.get("text")
            if isinstance(text, str) and text.strip():
                return text.strip()
    return ""
