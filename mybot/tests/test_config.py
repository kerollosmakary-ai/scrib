from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import ROOT_DIR, Settings, validate_settings


class ValidateSettingsTest(unittest.TestCase):
    def make_settings(self, generated_dir: Path) -> Settings:
        return Settings(
            telegram_token="token",
            admin_ids={1},
            use_local_ai=True,
            model_path=ROOT_DIR / "model.gguf",
            max_tokens=128,
            temperature=0.3,
            safety_prefix="1 ",
            remote_ai_url="",
            remote_ai_token="",
            generated_dir=generated_dir,
            expected_dir_name="mybot",
        )

    def test_accepts_generated_dir_under_mybot_root(self) -> None:
        validate_settings(self.make_settings(ROOT_DIR / "generated" / "bots"))

    def test_rejects_generated_dir_outside_mybot_root(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "GENERATED_DIR"):
            validate_settings(self.make_settings(ROOT_DIR.parent / "generated"))
