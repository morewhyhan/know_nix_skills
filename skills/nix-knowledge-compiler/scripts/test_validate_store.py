from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_store import LEGACY_SECTIONS, MECHANISM_SECTIONS, validate_store  # noqa: E402


def _links(values: list[str], relation: str) -> str:
    if not values:
        return "无"
    return "\n".join(f"- [[{value}]] - {relation}：fixture" for value in values)


def make_body(
    *,
    body_depends: list[str] | None = None,
    body_components: list[str] | None = None,
    status: str = "draft",
    legacy: bool = False,
    unresolved: str = "待验证：无",
) -> str:
    body_depends = body_depends or []
    body_components = body_components or []
    contents = {
        "场景用途": "用于验证 fixture。",
        "CLC方向": (
            "CLC全表扫描：已检查 A、B、C、D、E、F、G、H、I、J、K、N、O、P、Q、R、S、T、U、V、X、Z 22 个基本大类。\n"
            "主类：C93/管理学。\n展开与排除：fixture。"
        ),
        "定义": "这是一个可验证机制。与普通描述的区别：它有因果结构。排除：纯标签。",
        "边界": "不适用于缺少触发条件的场景。",
        "机制核心": "```text\n函数签名：原始状态 -> fixture 操作 -> 可观察输出\n\n触发条件 → 中介机制 → 可观察结果 → 适用边界\n```",
        "参与角色": "| 角色 | 说明 |\n|---|---|\n| 参与者 | 承担 fixture 功能 |",
        "成立条件": "1. 条件存在。",
        "迁移边界": "可迁移到：领域甲、领域乙。不能迁移到：无同构角色的领域。假迁移警惕：不能只换词。",
        "复用价值": "可供未来 fixture 调用。调用方式：检查触发、过程和结果。",
        "领域绑定": (
            "| 领域 | 映射 | 验证状态 | 证据定位 |\n"
            "|---|---|---|---|\n"
            "| fixture | fixture | 来源支持 | source.md |\n"
            + ("| independent fixture | fixture | 独立材料验证 | source-2.md |" if status == "stable" else "")
        ),
        "脱域说明": "去掉领域名后机制仍完整。",
        "区分说明": "暂无旧原子可准确承载。",
        "必要说明": (
            f"证据状态：{'多源互证' if status == 'stable' else '单一来源'}。\n"
            "来源支持：fixture source。\n"
            "编译器推导：由 fixture 推导。\n"
            f"{unresolved}\n"
            "学术线索：fixture theory。\n"
            "命名依据：描述性命名；已核验 C93/管理学。\n"
            "常见别名：别名甲，别名乙。\n"
            f"独立语义复核：{'通过；范围：完整 fixture' if status == 'stable' else '未执行；原因：fixture draft'}。"
            + ("\n去向：无替代。\n迁移理由：历史 fixture 已停止使用。" if status in {"deprecated", "merged"} else "")
        ),
        "依赖": _links(body_depends, "prerequisite"),
        "组件": _links(body_components, "composed_of"),
    }
    sections = LEGACY_SECTIONS if legacy and status in {"deprecated", "merged"} else MECHANISM_SECTIONS
    rendered = ["# Fixture"]
    for section in sections:
        rendered.extend(("", f"## {section}", "", contents[section]))
    return "\n".join(rendered) + "\n"


def write_atom(
    atoms_dir: Path,
    atom_id: str,
    *,
    status: str = "draft",
    source: str | list[str] = "source.md",
    depends_on: list[str] | None = None,
    components: list[str] | None = None,
    body_depends: list[str] | None = None,
    body_components: list[str] | None = None,
    include_aliases: bool = True,
    tags: list[str] | None = None,
    legacy: bool = False,
    unresolved: str = "待验证：无",
) -> Path:
    depends_on = depends_on or []
    components = components or []
    tags = tags or ["C93/管理学"]
    body_depends = depends_on if body_depends is None else body_depends
    body_components = components if body_components is None else body_components

    if isinstance(source, list):
        source_value = "[" + ", ".join(source) + "]"
    else:
        source_value = source
    fields = [
        f"id: {atom_id}",
        f"status: {status}",
        f"source: {source_value}",
        "tags: [" + ", ".join(tags) + "]",
    ]
    if include_aliases:
        fields.append("aliases: [别名甲, 别名乙]")
    fields.extend(
        (
            "depends_on: [" + ", ".join(depends_on) + "]",
            "components: [" + ", ".join(components) + "]",
        )
    )
    text = "---\n" + "\n".join(fields) + "\n---\n\n"
    text += make_body(
        body_depends=body_depends,
        body_components=body_components,
        status=status,
        legacy=legacy,
        unresolved=unresolved,
    )
    path = atoms_dir / f"{atom_id}.md"
    path.write_text(text, encoding="utf-8")
    return path


def write_reconstruction(
    root: Path,
    *,
    source: str = "source.md",
    mapped_atom: str | None = None,
    source_hash: str | None = None,
) -> Path:
    source_path = root / source
    digest = source_hash or hashlib.sha256(source_path.read_bytes()).hexdigest()
    mapping = f"| 来源机制 | 新建 | [[{mapped_atom}]] | fixture 映射 |" if mapped_atom else "| 来源观点 | 仅还原 | 无 | fixture 保留 |"
    text = f'''---
source: "{source}"
source_sha256: "{digest}"
---

# Fixture reconstruction

## 核心结论

这是足以独立理解来源的核心结论 fixture。

## 论证链

1. 前提经过推理产生可检查的来源结论。

## 关键概念

| 概念 | 含义 | 作用 |
|---|---|---|
| fixture | 来源定义 | 支撑论证 |

## 建议与适用范围

- 建议只适用于 fixture 边界。

## 证据与文本问题

- 作者断言：fixture。
- 原文替代验收：未执行；原因：fixture draft。

## 机制 atom 映射

| 内容 | 处理 | atom | 理由 |
|---|---|---|---|
{mapping}
'''
    path = root / "reconstructions" / "fixture--00000000.md"
    path.write_text(text, encoding="utf-8")
    return path


class ValidateStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.atoms = self.root / "atoms"
        self.atoms.mkdir()
        self.reconstructions = self.root / "reconstructions"
        self.reconstructions.mkdir()
        (self.root / "source.md").write_text("fixture source", encoding="utf-8")
        (self.root / "source-2.md").write_text("independent fixture source", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def error_codes(self) -> set[str]:
        return {issue.code for issue in validate_store(self.root).errors}

    def test_valid_fixture(self) -> None:
        write_atom(self.atoms, "有效原子", status="stable", source=["source.md", "source-2.md"])

        result = validate_store(self.root)

        self.assertTrue(result.ok, [issue.render("ERROR") for issue in result.errors])
        self.assertEqual(result.atom_count, 1)
        self.assertEqual(result.warnings, [])

    def test_valid_reconstruction_is_counted(self) -> None:
        write_atom(self.atoms, "还原映射原子", source=["source.md"])
        write_reconstruction(self.root, mapped_atom="还原映射原子")

        result = validate_store(self.root)

        self.assertTrue(result.ok, [issue.render("ERROR") for issue in result.errors])
        self.assertEqual(result.reconstruction_count, 1)

    def test_stale_reconstruction_hash_is_rejected(self) -> None:
        write_reconstruction(self.root, source_hash="0" * 64)

        self.assertIn("RECONSTRUCTION_STALE", self.error_codes())

    def test_reconstruction_missing_section_is_rejected(self) -> None:
        path = write_reconstruction(self.root)
        text = path.read_text(encoding="utf-8").replace("## 建议与适用范围", "### 建议与适用范围")
        path.write_text(text, encoding="utf-8")

        self.assertIn("RECONSTRUCTION_SECTIONS", self.error_codes())

    def test_reconstruction_missing_atom_link_is_rejected(self) -> None:
        write_reconstruction(self.root, mapped_atom="不存在的原子")

        self.assertIn("RECONSTRUCTION_LINK", self.error_codes())

    def test_clc_scan_must_be_recorded_in_body(self) -> None:
        path = write_atom(self.atoms, "缺少CLC全表扫描", source=["source.md"])
        text = path.read_text(encoding="utf-8").replace("CLC全表扫描", "只看常用方向")
        path.write_text(text, encoding="utf-8")

        self.assertIn("CLC_SCAN", self.error_codes())

    def test_missing_field(self) -> None:
        write_atom(self.atoms, "缺字段", include_aliases=False, source=["source.md"])

        self.assertIn("MISSING_FIELD", self.error_codes())

    def test_extra_frontmatter_field_is_rejected(self) -> None:
        path = write_atom(self.atoms, "多余字段", source=["source.md"])
        text = path.read_text(encoding="utf-8").replace("status: draft", "status: draft\nlevel: L1")
        path.write_text(text, encoding="utf-8")

        self.assertIn("EXTRA_FIELD", self.error_codes())

    def test_invalid_status_is_rejected(self) -> None:
        path = write_atom(self.atoms, "错误状态", source=["source.md"])
        text = path.read_text(encoding="utf-8").replace("status: draft", "status: ready")
        path.write_text(text, encoding="utf-8")

        self.assertIn("STATUS_INVALID", self.error_codes())

    def test_alias_cardinality_is_enforced(self) -> None:
        path = write_atom(self.atoms, "别名过多", source=["source.md"])
        text = path.read_text(encoding="utf-8").replace(
            "aliases: [别名甲, 别名乙]",
            "aliases: [甲, 乙, 丙, 丁, 戊, 己, 庚]",
        )
        path.write_text(text, encoding="utf-8")

        self.assertIn("FIELD_CARDINALITY", self.error_codes())

    def test_filename_must_match_id(self) -> None:
        path = write_atom(self.atoms, "原始文件名", source=["source.md"])
        path.rename(self.atoms / "错误文件名.md")

        self.assertIn("FILENAME_MISMATCH", self.error_codes())

    def test_source_must_be_nonempty_list(self) -> None:
        write_atom(self.atoms, "坏来源类型", source="source.md")

        self.assertIn("FIELD_TYPE", self.error_codes())

    def test_bad_source_path(self) -> None:
        write_atom(self.atoms, "坏来源", source=["missing.md"])

        self.assertIn("SOURCE_NOT_FOUND", self.error_codes())

    def test_tag_must_use_bundled_classification(self) -> None:
        write_atom(self.atoms, "坏标签", source=["source.md"], tags=["随手自创标签"])

        self.assertIn("TAG_NOT_ALLOWED", self.error_codes())

    def test_evidence_status_must_use_canonical_value(self) -> None:
        path = write_atom(self.atoms, "坏证据状态", source=["source.md"])
        text = path.read_text(encoding="utf-8").replace("证据状态：单一来源", "证据状态：source-derived")
        path.write_text(text, encoding="utf-8")

        self.assertIn("EVIDENCE_STATUS", self.error_codes())

    def test_aliases_must_match_necessary_section(self) -> None:
        path = write_atom(self.atoms, "别名漂移", source=["source.md"])
        text = path.read_text(encoding="utf-8").replace("常见别名：别名甲，别名乙", "常见别名：另一别名，完全不同")
        path.write_text(text, encoding="utf-8")

        self.assertIn("ALIAS_MISMATCH", self.error_codes())

    def test_duplicate_necessary_label_is_rejected(self) -> None:
        path = write_atom(self.atoms, "重复复核标签", source=["source.md"])
        text = path.read_text(encoding="utf-8").replace(
            "独立语义复核：未执行；原因：fixture draft。",
            "独立语义复核：未执行；原因：fixture draft。\n独立语义复核：通过；范围：另一份声明。",
        )
        path.write_text(text, encoding="utf-8")

        self.assertIn("NECESSARY_CONTENT", self.error_codes())

    def test_missing_link_target(self) -> None:
        write_atom(self.atoms, "坏链接", source=["source.md"], depends_on=["不存在"])

        self.assertIn("MISSING_TARGET", self.error_codes())

    def test_union_cycle_across_dependency_and_component_edges(self) -> None:
        write_atom(self.atoms, "原子甲", source=["source.md"], depends_on=["原子乙"])
        write_atom(self.atoms, "原子乙", source=["source.md"], components=["原子甲"])

        self.assertIn("GRAPH_CYCLE", self.error_codes())

    def test_self_loop_is_rejected(self) -> None:
        write_atom(self.atoms, "自环原子", source=["source.md"], depends_on=["自环原子"])

        self.assertIn("SELF_LOOP", self.error_codes())

    def test_duplicate_id_is_rejected(self) -> None:
        path = write_atom(self.atoms, "重复身份", source=["source.md"])
        (self.atoms / "另一个文件.md").write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

        self.assertIn("DUPLICATE_ID", self.error_codes())

    def test_frontmatter_and_body_links_must_match(self) -> None:
        write_atom(self.atoms, "原子乙", source=["source.md"])
        write_atom(
            self.atoms,
            "正文不同步",
            source=["source.md"],
            depends_on=["原子乙"],
            body_depends=[],
        )

        self.assertIn("BODY_LINK_MISMATCH", self.error_codes())

    def test_dependency_relation_type_is_checked(self) -> None:
        write_atom(self.atoms, "原子乙", source=["source.md"])
        path = write_atom(self.atoms, "错误关系类型", source=["source.md"], depends_on=["原子乙"])
        text = path.read_text(encoding="utf-8").replace("- [[原子乙]] - prerequisite：fixture", "- [[原子乙]] - composed_of：fixture reason")
        path.write_text(text, encoding="utf-8")

        self.assertIn("RELATION_TYPE", self.error_codes())

    def test_relation_reason_is_required(self) -> None:
        write_atom(self.atoms, "原子乙", source=["source.md"])
        path = write_atom(self.atoms, "缺关系理由", source=["source.md"], depends_on=["原子乙"])
        text = path.read_text(encoding="utf-8").replace("prerequisite：fixture", "prerequisite：无")
        path.write_text(text, encoding="utf-8")

        self.assertIn("RELATION_REASON", self.error_codes())

    def test_stable_atom_rejects_unresolved_items(self) -> None:
        write_atom(
            self.atoms,
            "未决稳定原子",
            status="stable",
            source=["source.md", "source-2.md"],
            unresolved="待验证：需要独立材料",
        )

        self.assertIn("STABLE_UNRESOLVED", self.error_codes())

    def test_stable_atom_requires_two_sources(self) -> None:
        write_atom(self.atoms, "单源稳定原子", status="stable", source=["source.md"])

        self.assertIn("STABLE_EVIDENCE", self.error_codes())

    def test_stable_semantic_review_rejects_placeholder_scope(self) -> None:
        path = write_atom(
            self.atoms,
            "复核范围占位",
            status="stable",
            source=["source.md", "source-2.md"],
        )
        text = path.read_text(encoding="utf-8").replace(
            "独立语义复核：通过；范围：完整 fixture。",
            "独立语义复核：通过；范围：...。",
        )
        path.write_text(text, encoding="utf-8")

        self.assertIn("SEMANTIC_REVIEW", self.error_codes())

    def test_stable_requires_substantive_source_support(self) -> None:
        path = write_atom(
            self.atoms,
            "无来源支持",
            status="stable",
            source=["source.md", "source-2.md"],
        )
        text = path.read_text(encoding="utf-8").replace("来源支持：fixture source。", "来源支持：无。")
        path.write_text(text, encoding="utf-8")

        self.assertIn("STABLE_EVIDENCE", self.error_codes())

    def test_stable_does_not_accept_negated_binding_substring(self) -> None:
        path = write_atom(
            self.atoms,
            "否定式伪验证",
            status="stable",
            source=["source.md", "source-2.md"],
        )
        text = path.read_text(encoding="utf-8").replace("| 独立材料验证 |", "| 不存在独立材料验证 |")
        path.write_text(text, encoding="utf-8")

        codes = self.error_codes()
        self.assertIn("BINDING_STATUS", codes)
        self.assertIn("STABLE_EVIDENCE", codes)

    def test_stable_binding_evidence_must_reference_source(self) -> None:
        path = write_atom(
            self.atoms,
            "伪证据定位",
            status="stable",
            source=["source.md", "source-2.md"],
        )
        text = path.read_text(encoding="utf-8").replace(
            "| independent fixture | fixture | 独立材料验证 | source-2.md |",
            "| independent fixture | fixture | 独立材料验证 | fictional.md |",
        )
        path.write_text(text, encoding="utf-8")

        self.assertIn("STABLE_EVIDENCE", self.error_codes())

    def test_stable_independent_binding_must_use_different_source(self) -> None:
        path = write_atom(
            self.atoms,
            "同源伪独立验证",
            status="stable",
            source=["source.md", "source-2.md"],
        )
        text = path.read_text(encoding="utf-8").replace(
            "| independent fixture | fixture | 独立材料验证 | source-2.md |",
            "| independent fixture | fixture | 独立材料验证 | source.md |",
        )
        path.write_text(text, encoding="utf-8")

        self.assertIn("STABLE_EVIDENCE", self.error_codes())

    def test_stable_sources_must_have_distinct_content(self) -> None:
        (self.root / "source-2.md").write_text("fixture source", encoding="utf-8")
        write_atom(
            self.atoms,
            "复制文件伪独立来源",
            status="stable",
            source=["source.md", "source-2.md"],
        )

        self.assertIn("STABLE_EVIDENCE", self.error_codes())

    def test_stable_deduplicates_relative_and_absolute_source(self) -> None:
        absolute = str((self.root / "source.md").resolve()).replace("\\", "/")
        write_atom(
            self.atoms,
            "重复来源身份",
            status="stable",
            source=["source.md", absolute],
        )

        self.assertIn("STABLE_EVIDENCE", self.error_codes())

    def test_stable_does_not_count_unfetched_urls(self) -> None:
        write_atom(
            self.atoms,
            "未抓取网址来源",
            status="stable",
            source=["https://example.com/a", "https://example.org/b"],
        )

        self.assertIn("STABLE_EVIDENCE", self.error_codes())

    def test_mechanism_signature_is_required(self) -> None:
        path = write_atom(self.atoms, "缺函数签名", source=["source.md"])
        text = path.read_text(encoding="utf-8").replace("函数签名：原始状态 -> fixture 操作 -> 可观察输出\n\n", "")
        path.write_text(text, encoding="utf-8")

        self.assertIn("MECHANISM_SIGNATURE", self.error_codes())

    def test_empty_shell_sections_are_rejected(self) -> None:
        path = write_atom(self.atoms, "空壳机制", source=["source.md"])
        text = path.read_text(encoding="utf-8").replace("用于验证 fixture。", "无")
        path.write_text(text, encoding="utf-8")

        self.assertIn("SECTION_CONTENT", self.error_codes())

    def test_section_order_is_enforced(self) -> None:
        path = write_atom(self.atoms, "章节顺序错误", source=["source.md"])
        text = path.read_text(encoding="utf-8").replace("## 场景用途", "## CLC方向", 1)
        path.write_text(text, encoding="utf-8")

        self.assertIn("SECTION_ORDER", self.error_codes())

    def test_machine_structure_inside_fence_is_ignored(self) -> None:
        path = write_atom(self.atoms, "代码块伪结构", source=["source.md"])
        text = path.read_text(encoding="utf-8")
        closing = text.find("\n---\n", 4) + len("\n---\n")
        text = text[:closing] + "\n````markdown\n" + text[closing:] + "\n````\n"
        path.write_text(text, encoding="utf-8")

        self.assertIn("SECTION_ORDER", self.error_codes())

    def test_deprecated_legacy_sections_are_allowed_with_warning(self) -> None:
        write_atom(
            self.atoms,
            "旧原子",
            status="deprecated",
            source=["source.md"],
            legacy=True,
        )

        result = validate_store(self.root)

        self.assertTrue(result.ok, [issue.render("ERROR") for issue in result.errors])
        self.assertIn("LEGACY_SECTIONS", {issue.code for issue in result.warnings})

    def test_merged_atom_requires_existing_destination(self) -> None:
        path = write_atom(
            self.atoms,
            "已合并原子",
            status="merged",
            source=["source.md"],
            legacy=True,
        )
        text = path.read_text(encoding="utf-8").replace("去向：无替代", "去向：[[不存在原子]]")
        path.write_text(text, encoding="utf-8")

        self.assertIn("LIFECYCLE_TARGET", self.error_codes())

    def test_merged_destination_cycle_is_rejected(self) -> None:
        first = write_atom(self.atoms, "合并甲", status="merged", source=["source.md"], legacy=True)
        second = write_atom(self.atoms, "合并乙", status="merged", source=["source.md"], legacy=True)
        first.write_text(first.read_text(encoding="utf-8").replace("去向：无替代", "去向：[[合并乙]]"), encoding="utf-8")
        second.write_text(second.read_text(encoding="utf-8").replace("去向：无替代", "去向：[[合并甲]]"), encoding="utf-8")

        self.assertIn("LIFECYCLE_CYCLE", self.error_codes())


if __name__ == "__main__":
    unittest.main()
