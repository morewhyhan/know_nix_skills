#!/usr/bin/env python3
"""Rollback tests for commit_batch.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from commit_batch import commit  # noqa: E402


def mechanism(title: str, relation: str = "- 暂无正式关系。") -> str:
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

包含合理迁移与错误迁移。

## 来源与证据

| 内容 | 证据角色 | 来源或定位 | 当前结论 |
|---|---|---|---|
| 机制 | 系统推导 | 集成测试 | draft |

## 关系

{relation}

## 候选关联

- 暂无。
"""


class CommitBatchTests(unittest.TestCase):
    def test_successful_batch_is_committed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "workspace"
            staging = Path(temp) / "staging"
            source = staging / "knowledge" / "analyses" / "note.md"
            source.parent.mkdir(parents=True)
            source.write_text("# committed", encoding="utf-8")

            commit(root, staging)

            target = root / "knowledge" / "analyses" / "note.md"
            self.assertEqual(target.read_text(encoding="utf-8"), "# committed")

    def test_simulated_failure_restores_changed_and_new_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "workspace"
            staging = Path(temp) / "staging"
            old = root / "knowledge" / "mechanisms" / "old.md"
            old.parent.mkdir(parents=True)
            old.write_text("before", encoding="utf-8")

            staged_old = staging / "knowledge" / "mechanisms" / "old.md"
            staged_new = staging / "knowledge" / "mechanisms" / "new.md"
            staged_old.parent.mkdir(parents=True)
            staged_old.write_text("after", encoding="utf-8")
            staged_new.write_text("new", encoding="utf-8")

            with self.assertRaises(RuntimeError):
                commit(root, staging, fail_after=2)

            self.assertEqual(old.read_text(encoding="utf-8"), "before")
            self.assertFalse((old.parent / "new.md").exists())

    def test_validation_failure_removes_new_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "workspace"
            staging = Path(temp) / "staging"
            invalid = staging / "knowledge" / "mechanisms" / "invalid.md"
            invalid.parent.mkdir(parents=True)
            invalid.write_text("# invalid", encoding="utf-8")

            with self.assertRaises(RuntimeError):
                commit(root, staging)

            self.assertFalse((root / "knowledge" / "mechanisms" / "invalid.md").exists())

    def test_configured_store_root_is_committed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "workspace"
            staging = Path(temp) / "staging"
            root.mkdir(parents=True)
            (root / ".mechanism-network.yml").write_text(
                "version: \"0.1\"\nstore_root: vault/mechanisms\n", encoding="utf-8"
            )
            source = staging / "vault" / "mechanisms" / "analyses" / "note.md"
            source.parent.mkdir(parents=True)
            source.write_text("# configured", encoding="utf-8")

            commit(root, staging)

            target = root / "vault" / "mechanisms" / "analyses" / "note.md"
            self.assertEqual(target.read_text(encoding="utf-8"), "# configured")

    def test_complete_multi_file_batch_commits_with_reciprocal_link(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "workspace"
            staging = Path(temp) / "staging"
            live = root / "knowledge" / "mechanisms" / "反馈学习.md"
            live.parent.mkdir(parents=True)
            live.write_text(mechanism("反馈学习"), encoding="utf-8")

            staged_mechanisms = staging / "knowledge" / "mechanisms"
            staged_mechanisms.mkdir(parents=True)
            forward = "- `约束` → [[反馈学习]]：理由：延迟会改变反馈可用性；边界：不代表反馈必然失真；证据：系统推导。"
            backward = "- `约束` ← [[延迟反馈]]：理由：更新速度受反馈到达时间限制；边界：延迟不是唯一误差来源；证据：系统推导。"
            (staged_mechanisms / "延迟反馈.md").write_text(
                mechanism("延迟反馈", forward), encoding="utf-8"
            )
            (staged_mechanisms / "反馈学习.md").write_text(
                mechanism("反馈学习", backward), encoding="utf-8"
            )

            reconstruction = staging / "knowledge" / "reconstructions" / "测试材料.md"
            reconstruction.parent.mkdir(parents=True)
            reconstruction.write_text(
                """# 来源还原：测试材料

## 一句话还原
测试。
## 原始材料表达了什么
测试。
## 论证或叙述怎样展开
测试。
## 用户增加了什么
测试。
## 系统可以合理推导什么
测试。
## 不能从材料推出什么
测试。
## 事实、证据与文本风险
测试。
## 机制处理决策
测试。
""",
                encoding="utf-8",
            )
            report = staging / "knowledge" / "runs" / "测试运行.md"
            report.parent.mkdir(parents=True)
            report.write_text(
                """# 知识库运行报告：测试

## 读取内容
测试。
## 来源还原
测试。
## 机制卡变更
测试。
## 关系变更
测试。
## 跨系统组合
测试。
## 验收
测试。
## 仍待验证
测试。
""",
                encoding="utf-8",
            )

            commit(root, staging)

            self.assertTrue((root / "knowledge" / "mechanisms" / "延迟反馈.md").exists())
            self.assertIn("[[延迟反馈]]", live.read_text(encoding="utf-8"))
            self.assertTrue((root / "knowledge" / "reconstructions" / "测试材料.md").exists())
            self.assertTrue((root / "knowledge" / "runs" / "测试运行.md").exists())


if __name__ == "__main__":
    unittest.main()
