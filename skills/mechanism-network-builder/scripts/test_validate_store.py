#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("validate_store.py")
SPEC = importlib.util.spec_from_file_location("validate_store", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def mechanism(title: str, target: str) -> str:
    return f"""---
type: mechanism
status: draft
aliases: []
created: 2026-07-14
updated: 2026-07-14
---

# {title}

> 一句话说明用途。

## 它解决什么问题

解决一个可检查的问题。

## 怎么起作用

输入 → 作用 → 中介 → 结果

## 参与角色

| 角色 | 作用 |
|---|---|
| 系统 | 执行变化 |

## 什么时候成立

- 条件成立。

## 什么时候失效

- 条件不成立。

## 新场景测试

合理迁移与错误迁移都已说明。

## 来源与证据

| 内容 | 证据角色 | 来源或定位 | 当前结论 |
|---|---|---|---|
| 机制 | 系统推导 | 测试 | draft |

## 关系

- `对照` → [[{target}]]：理由：两者策略不同；边界：不代表互斥；证据：系统推导。

## 候选关联

- 暂无。
"""


class ValidatorTests(unittest.TestCase):
    def make_store(self, root: Path) -> tuple[Path, Path]:
        cards = root / "knowledge" / "mechanisms"
        cards.mkdir(parents=True)
        a = cards / "机制甲.md"
        b = cards / "机制乙.md"
        a.write_text(mechanism("机制甲", "机制乙"), encoding="utf-8")
        b.write_text(mechanism("机制乙", "机制甲"), encoding="utf-8")
        return a, b

    def test_valid_reciprocal_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_store(root)
            self.assertEqual([], MODULE.validate_store(root))

    def test_unresolved_link_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a, _b = self.make_store(root)
            a.write_text(mechanism("机制甲", "不存在"), encoding="utf-8")
            messages = [issue.message for issue in MODULE.validate_store(root)]
            self.assertTrue(any("无法解析 wikilink" in message for message in messages))

    def test_filename_title_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a, _b = self.make_store(root)
            a.write_text(mechanism("错误标题", "机制乙"), encoding="utf-8")
            messages = [issue.message for issue in MODULE.validate_store(root)]
            self.assertTrue(any("文件名与 H1 不一致" in message for message in messages))

    def test_candidate_wikilink_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a, _b = self.make_store(root)
            text = a.read_text(encoding="utf-8").replace("- 暂无。", "- [[机制乙]]")
            a.write_text(text, encoding="utf-8")
            messages = [issue.message for issue in MODULE.validate_store(root)]
            self.assertTrue(any("候选关联不得包含" in message for message in messages))

    def test_relation_requires_reason_boundary_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a, _b = self.make_store(root)
            text = a.read_text(encoding="utf-8").replace(
                "理由：两者策略不同；边界：不代表互斥；证据：系统推导。",
                "两者有关系。",
            )
            a.write_text(text, encoding="utf-8")
            messages = [issue.message for issue in MODULE.validate_store(root)]
            self.assertTrue(any("正式关系缺少字段" in message for message in messages))

    def test_relation_must_target_exactly_one_card(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a, _b = self.make_store(root)
            text = a.read_text(encoding="utf-8").replace(
                "[[机制乙]]", "[[机制乙]]、[[机制甲]]"
            )
            a.write_text(text, encoding="utf-8")
            messages = [issue.message for issue in MODULE.validate_store(root)]
            self.assertTrue(any("只能指向一张" in message for message in messages))

    def test_isolated_card_may_have_no_formal_relation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cards = root / "knowledge" / "mechanisms"
            cards.mkdir(parents=True)
            text = mechanism("孤立机制", "不存在").replace(
                "- `对照` → [[不存在]]：理由：两者策略不同；边界：不代表互斥；证据：系统推导。",
                "- 暂无正式关系。",
            )
            (cards / "孤立机制.md").write_text(text, encoding="utf-8")
            self.assertEqual([], MODULE.validate_store(root))

    def test_configured_store_root_is_honored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".mechanism-network.yml").write_text(
                "version: \"0.1\"\nstore_root: vault/cards\n", encoding="utf-8"
            )
            cards = root / "vault" / "cards" / "mechanisms"
            cards.mkdir(parents=True)
            (cards / "机制甲.md").write_text(mechanism("机制甲", "机制乙"), encoding="utf-8")
            (cards / "机制乙.md").write_text(mechanism("机制乙", "机制甲"), encoding="utf-8")
            self.assertEqual([], MODULE.validate_store(root))

    def test_unresolved_link_in_analysis_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_store(root)
            analysis = root / "knowledge" / "analyses" / "分析.md"
            analysis.parent.mkdir(parents=True)
            analysis.write_text("# 分析\n\n[[不存在]]", encoding="utf-8")
            messages = [issue.message for issue in MODULE.validate_store(root)]
            self.assertTrue(any("无法解析 wikilink" in message for message in messages))

    def test_duplicate_non_card_note_title_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_store(root)
            one = root / "knowledge" / "analyses" / "重复.md"
            two = root / "knowledge" / "runs" / "重复.md"
            one.parent.mkdir(parents=True)
            two.parent.mkdir(parents=True)
            one.write_text("# 重复", encoding="utf-8")
            two.write_text("# 重复", encoding="utf-8")
            messages = [issue.message for issue in MODULE.validate_store(root)]
            self.assertTrue(any("笔记标题不唯一" in message for message in messages))


if __name__ == "__main__":
    unittest.main()
