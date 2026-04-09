from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from funding_arb.utils.config import load_config


class ConfigLoaderTests(unittest.TestCase):
    def test_load_config_reads_mapping(self) -> None:
        temp_dir = Path("tests/fixtures")
        temp_dir.mkdir(parents=True, exist_ok=True)
        config_path = temp_dir / "_tmp_test_config.json"
        try:
            config_path.write_text('{"section": {"value": 42}}', encoding="utf-8")
            loaded = load_config(config_path)
            self.assertEqual(loaded["section"]["value"], 42)
        finally:
            if config_path.exists():
                config_path.unlink()


if __name__ == "__main__":
    unittest.main()
