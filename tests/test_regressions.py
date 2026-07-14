#!/usr/bin/env python3
"""Semantic regression checks for the bundled golden cases."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
import re
from urllib.parse import unquote

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPT_DIR = ROOT / "skills" / "mechanism-network-builder" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from validate_store import validate_store  # noqa: E402


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class GoldenRegressionTests(unittest.TestCase):
    def test_live_store_is_structurally_valid(self) -> None:
        issues = validate_store(ROOT)
        self.assertEqual([], [issue.render(ROOT) for issue in issues])

    def test_first_case_keeps_source_and_extension_separate(self) -> None:
        reconstruction = read(
            "golden-cases/001-shenxiu-huineng/expected/00-source-reconstruction.md"
        )
        self.assertIn("不能", reconstruction)
        self.assertIn("反脆弱", reconstruction)
        self.assertIn("现代延伸", reconstruction)
        self.assertIn("不能挂在慧能名下", reconstruction)

    def test_all_21_first_case_wikilinks_resolve_inside_case(self) -> None:
        case = ROOT / "golden-cases" / "001-shenxiu-huineng"
        files = list(case.rglob("*.md"))
        self.assertEqual(21, len(files))
        card_names = {path.stem for path in (case / "expected" / "cards").glob("*.md")}
        unresolved: list[tuple[str, str]] = []
        for path in files:
            for target in re.findall(r"\[\[([^\]|#]+)", path.read_text(encoding="utf-8")):
                if target not in card_names:
                    unresolved.append((str(path.relative_to(case)), target))
        self.assertEqual([], unresolved)

    def test_antifragility_does_not_collapse_into_resilience(self) -> None:
        card = read("knowledge/systems/反脆弱.md")
        self.assertIn("从波动增加中获得更多净收益", card)
        self.assertIn("这是韧性，不是反脆弱", card)

    def test_second_case_reuses_problem_reframing(self) -> None:
        report = read("knowledge/runs/2026-07-14-regression-002-flood-diversion.md")
        self.assertIn("复用并更新关系 | [[问题重构]]", report)
        self.assertFalse((ROOT / "knowledge/mechanisms/跳出二选一.md").exists())

    def test_second_case_rejects_trolley_equivalence_and_forced_antifragility(self) -> None:
        reconstruction = read("knowledge/reconstructions/要不要打开分洪闸.md")
        self.assertIn("不能证明所有集体风险决策都与电车难题同构", reconstruction)
        for name in ("分配正义", "程序正义", "鲁棒决策", "双重效应原则", "公共风险四重审查"):
            folder = "systems" if name == "公共风险四重审查" else "mechanisms"
            self.assertNotIn("[[反脆弱]]", read(f"knowledge/{folder}/{name}.md"))

    def test_second_combination_has_distinct_inputs_and_new_process(self) -> None:
        system = read("knowledge/systems/公共风险四重审查.md")
        for name in ("鲁棒决策", "分配正义", "程序正义", "双重效应原则", "问题重构"):
            self.assertIn(f"[[{name}]]", system)
        self.assertIn("多情境压力测试", system)
        self.assertIn("第三方案", system)

    def test_no_mechanism_fixture_builds_no_card(self) -> None:
        decision = read("golden-cases/003-no-mechanism/expected-decision.md")
        self.assertIn("新建机制卡：否", decision)
        self.assertFalse((ROOT / "knowledge/mechanisms/雨天咖啡提升心情.md").exists())
        self.assertFalse((ROOT / "knowledge/mechanisms/蓝杯效应.md").exists())

    def test_local_markdown_links_resolve(self) -> None:
        roots = [ROOT / "README.md", ROOT / "specs", ROOT / "skills" / "mechanism-network-builder"]
        files: list[Path] = []
        for item in roots:
            files.extend(item.rglob("*.md") if item.is_dir() else [item])
        missing: list[tuple[str, str]] = []
        for path in files:
            text = path.read_text(encoding="utf-8")
            for target in re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", text):
                clean = unquote(target.split("#", 1)[0]).strip("<>")
                if not clean or re.match(r"^(?:https?|mailto):", clean):
                    continue
                if not (path.parent / clean).resolve().exists():
                    missing.append((str(path.relative_to(ROOT)), target))
        self.assertEqual([], missing)

    def test_installed_skill_package_shape_is_self_contained(self) -> None:
        skill = ROOT / "skills" / "mechanism-network-builder"
        self.assertTrue((skill / "SKILL.md").exists())
        self.assertTrue((skill / "agents" / "openai.yaml").exists())
        self.assertTrue((skill / "assets" / "mechanism-network.yml").exists())
        self.assertFalse((skill / "README.md").exists())
        metadata = (skill / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("$mechanism-network-builder", metadata)


if __name__ == "__main__":
    unittest.main()
