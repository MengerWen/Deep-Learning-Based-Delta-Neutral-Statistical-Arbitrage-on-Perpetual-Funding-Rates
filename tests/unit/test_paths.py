from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from funding_arb.utils.paths import REPO_ROOT, repo_path


class PathTests(unittest.TestCase):
    def test_repo_root_contains_agents_file(self) -> None:
        self.assertTrue((REPO_ROOT / "AGENTS.md").exists())

    def test_repo_path_resolves_from_root(self) -> None:
        self.assertTrue(repo_path("configs", "data", "default.yaml").exists())


if __name__ == "__main__":
    unittest.main()
