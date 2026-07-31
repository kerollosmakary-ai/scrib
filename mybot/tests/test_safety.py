from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from safety import is_command


class IsCommandTest(unittest.TestCase):
    def test_detects_telegram_commands(self) -> None:
        self.assertTrue(is_command("/help"))

    def test_ignores_regular_chat_text(self) -> None:
        self.assertFalse(is_command("explain this code"))
