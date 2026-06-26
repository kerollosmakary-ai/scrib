from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from storage import write_generated_bot


class WriteGeneratedBotTest(unittest.TestCase):
    def test_rejects_nested_file_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "basename"):
                write_generated_bot(Path(tmp), "nested/bot.py", "print('hi')\n")

    def test_writes_python_file_for_basename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            saved_path = write_generated_bot(Path(tmp), "bot.py", "print('hi')\n")

            self.assertEqual(Path(tmp) / "bot.py", saved_path)
            self.assertEqual("print('hi')\n", saved_path.read_text(encoding="utf-8"))
