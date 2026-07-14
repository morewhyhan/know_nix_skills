#!/usr/bin/env python3
"""Deterministic validator for a mechanism-network knowledge store."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


ALLOWED_TYPES = {"mechanism", "system"}
ALLOWED_STATUSES = {"draft", "usable", "stable", "retired"}
ALLOWED_RELATIONS = {
    "组成",
    "前置",
    "中介",
    "约束",
    "对照",
    "案例验证",
    "反例限定",
    "相关案例",
    "组合",
}
ALLOWED_EVIDENCE_ROLES = {
    "原文直接表达",
    "用户解释",
    "系统推导",
    "独立材料支持",
    "跨域推演",
    "组合设计",
    "反例限定",
}

MECHANISM_SECTIONS = [
    "它解决什么问题",
    "怎么起作用",
    "参与角色",
    "什么时候成立",
    "什么时候失效",
    "新场景测试",
    "来源与证据",
    "关系",
    "候选关联",
]

SYSTEM_SECTIONS = [
    "它解决什么新问题",
    "输入机制",
    "系统接口",
    "组合机制",
    "单个机制为什么做不到",
    "新增能力",
    "系统规则或设计",
    "应用测试",
    "失效与可推翻条件",
    "身份与证据",
    "关系",
    "候选关联",
]

RECONSTRUCTION_SECTIONS = [
    "一句话还原",
    "原始材料表达了什么",
    "论证或叙述怎样展开",
    "用户增加了什么",
    "系统可以合理推导什么",
    "不能从材料推出什么",
    "事实、证据与文本风险",
    "机制处理决策",
]

RUN_SECTIONS = [
    "读取内容",
    "来源还原",
    "机制卡变更",
    "关系变更",
    "跨系统组合",
    "验收",
    "仍待验证",
]

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
RELATION_LINE_RE = re.compile(r"^-\s+`([^`]+)`[^\n]*$", re.MULTILINE)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class Issue:
    path: Path
    message: str

    def render(self, root: Path) -> str:
        try:
            shown = self.path.relative_to(root)
        except ValueError:
            shown = self.path
        return f"{shown}: {self.message}"


def parse_frontmatter(text: str) -> tuple[dict[str, object], str, str | None]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text, "缺少 YAML frontmatter"
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return {}, text, "frontmatter 没有结束分隔符"

    data: dict[str, object] = {}
    active_list: str | None = None
    for raw in lines[1:end]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith("  - ") and active_list:
            assert isinstance(data[active_list], list)
            data[active_list].append(raw[4:].strip().strip('"\''))
            continue
        if ":" not in raw or raw.startswith(" "):
            return {}, "\n".join(lines[end + 1 :]), f"无法解析 frontmatter 行：{raw}"
        key, value = raw.split(":", 1)
        key = key.strip()
        value = value.strip()
        active_list = None
        if value == "[]":
            data[key] = []
        elif value == "":
            data[key] = []
            active_list = key
        else:
            data[key] = value.strip('"\'')
    return data, "\n".join(lines[end + 1 :]), None


def h1_title(body: str) -> str | None:
    match = re.search(r"^#\s+(.+?)\s*$", body, re.MULTILINE)
    return match.group(1).strip() if match else None


def sections(body: str) -> dict[str, str]:
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", body, re.MULTILINE))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        result[match.group(1).strip()] = body[start:end].strip()
    return result


def wikilinks(text: str) -> list[str]:
    return [match.group(1).strip() for match in WIKILINK_RE.finditer(text)]


def configured_store(root: Path) -> tuple[Path, str | None]:
    config = root / ".mechanism-network.yml"
    store_value = "knowledge"
    if config.exists():
        text = config.read_text(encoding="utf-8")
        match = re.search(r"^store_root:\s*(.+?)\s*$", text, re.MULTILINE)
        if not match:
            return root / store_value, "配置文件缺少 store_root"
        store_value = match.group(1).strip().strip('"\'')

    relative = Path(store_value)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        return root / "knowledge", f"非法 store_root：{store_value}"
    store = (root / relative).resolve()
    if root.resolve() not in store.parents:
        return root / "knowledge", f"store_root 超出 workspace：{store_value}"
    return store, None


def relation_records(section: str) -> list[tuple[str, list[str], str]]:
    records: list[tuple[str, list[str], str]] = []
    for match in RELATION_LINE_RE.finditer(section):
        line = match.group(0)
        records.append((match.group(1), wikilinks(line), line))
    return records


def card_files(store: Path) -> list[Path]:
    files: list[Path] = []
    for folder in ("mechanisms", "systems"):
        target = store / folder
        if target.exists():
            files.extend(sorted(target.rglob("*.md")))
    return files


def validate_card(path: Path, root: Path) -> tuple[list[Issue], dict[str, object], str]:
    issues: list[Issue] = []
    text = path.read_text(encoding="utf-8")
    meta, body, error = parse_frontmatter(text)
    if error:
        issues.append(Issue(path, error))
        return issues, meta, body

    required = {"type", "status", "aliases", "created", "updated"}
    missing = sorted(required - set(meta))
    if missing:
        issues.append(Issue(path, f"frontmatter 缺少字段：{', '.join(missing)}"))

    card_type = str(meta.get("type", ""))
    if card_type not in ALLOWED_TYPES:
        issues.append(Issue(path, f"非法 type：{card_type}"))
    status = str(meta.get("status", ""))
    if status not in ALLOWED_STATUSES:
        issues.append(Issue(path, f"非法 status：{status}"))
    if not isinstance(meta.get("aliases"), list):
        issues.append(Issue(path, "aliases 必须是列表"))
    for field in ("created", "updated"):
        value = str(meta.get(field, ""))
        if value and not DATE_RE.match(value):
            issues.append(Issue(path, f"{field} 必须使用 YYYY-MM-DD"))

    title = h1_title(body)
    if title is None:
        issues.append(Issue(path, "缺少 H1 标题"))
    elif title != path.stem:
        issues.append(Issue(path, f"文件名与 H1 不一致：{path.stem!r} != {title!r}"))

    first_h2 = re.search(r"^##\s+", body, re.MULTILINE)
    intro = body[: first_h2.start()] if first_h2 else body
    if not re.search(r"^>\s+\S", intro, re.MULTILINE):
        issues.append(Issue(path, "H1 后、首个 H2 前必须有一句白话说明"))

    parsed_sections = sections(body)
    expected = SYSTEM_SECTIONS if card_type == "system" else MECHANISM_SECTIONS
    for heading in expected:
        if heading not in parsed_sections:
            issues.append(Issue(path, f"缺少章节：{heading}"))
        elif not parsed_sections[heading].strip():
            issues.append(Issue(path, f"章节为空：{heading}"))

    candidate = parsed_sections.get("候选关联", "")
    if wikilinks(candidate):
        issues.append(Issue(path, "候选关联不得包含 wikilink"))

    if status == "retired" and "退休说明" not in parsed_sections:
        issues.append(Issue(path, "retired 卡必须包含“退休说明”章节"))

    relation_section = parsed_sections.get("关系", "")
    records = relation_records(relation_section)
    bullets = [line for line in relation_section.splitlines() if line.strip().startswith("-")]
    explicit_none = len(bullets) == 1 and bullets[0].strip() in {
        "- 暂无。",
        "- 暂无正式关系。",
    }
    if not explicit_none and len(records) != len(bullets):
        issues.append(Issue(path, "关系区每个项目都必须使用反引号标记关系类型"))
    for relation, targets, line in records:
        if relation not in ALLOWED_RELATIONS:
            issues.append(Issue(path, f"非法关系类型：{relation}"))
        if len(targets) != 1:
            issues.append(Issue(path, "每条正式关系必须且只能指向一张目标卡"))
        for label in ("理由：", "边界：", "证据："):
            if label not in line:
                issues.append(Issue(path, f"正式关系缺少字段：{label[:-1]}"))
        fields = re.search(r"理由：(.+?)；边界：(.+?)；证据：(.+?)(?:。)?$", line)
        if not fields or any(not value.strip() for value in fields.groups()):
            issues.append(Issue(path, "正式关系必须按“理由；边界；证据”填写非空内容"))
        elif not any(role in fields.group(3) for role in ALLOWED_EVIDENCE_ROLES):
            issues.append(Issue(path, "正式关系的证据字段必须包含合法证据角色"))

    return issues, meta, body


def validate_store(root: Path) -> list[Issue]:
    root = root.resolve()
    store, config_error = configured_store(root)
    issues: list[Issue] = []
    if config_error:
        issues.append(Issue(root / ".mechanism-network.yml", config_error))
        return issues
    if not store.exists():
        return [Issue(store, "知识库目录不存在")]

    cards = card_files(store)
    all_notes = sorted(store.rglob("*.md"))
    notes_by_name: dict[str, list[Path]] = {}
    for path in all_notes:
        notes_by_name.setdefault(path.stem, []).append(path)
    for name, paths in notes_by_name.items():
        if len(paths) > 1:
            for path in paths:
                issues.append(Issue(path, f"Obsidian 笔记标题不唯一：{name}"))

    by_name: dict[str, list[Path]] = {}
    bodies: dict[str, str] = {}
    for path in cards:
        by_name.setdefault(path.stem, []).append(path)
        card_issues, _meta, body = validate_card(path, root)
        issues.extend(card_issues)
        bodies[path.stem] = body

    for source_name, body in bodies.items():
        source_path = by_name[source_name][0]
        for target in wikilinks(body):
            if target not in notes_by_name:
                issues.append(Issue(source_path, f"无法解析 wikilink：{target}"))

        relation_section = sections(body).get("关系", "")
        for relation, targets, _line in relation_records(relation_section):
            if len(targets) != 1:
                continue
            target = targets[0]
            if target not in bodies:
                continue
            if f"[[{source_name}]]" not in bodies[target]:
                issues.append(
                    Issue(
                        source_path,
                        f"正式关系缺少反向链接：`{relation}` → [[{target}]]",
                    )
                )

    checked_content: set[Path] = set(cards)
    for folder, required in (("reconstructions", RECONSTRUCTION_SECTIONS), ("runs", RUN_SECTIONS)):
        target = store / folder
        if not target.exists():
            continue
        for path in sorted(target.rglob("*.md")):
            checked_content.add(path)
            text = path.read_text(encoding="utf-8")
            parsed = sections(text)
            for heading in required:
                if heading not in parsed:
                    issues.append(Issue(path, f"缺少章节：{heading}"))
                elif not parsed[heading].strip():
                    issues.append(Issue(path, f"章节为空：{heading}"))
            for target_name in wikilinks(text):
                if target_name not in notes_by_name:
                    issues.append(Issue(path, f"无法解析 wikilink：{target_name}"))

    for path in all_notes:
        if path in checked_content:
            continue
        text = path.read_text(encoding="utf-8")
        for target_name in wikilinks(text):
            if target_name not in notes_by_name:
                issues.append(Issue(path, f"无法解析 wikilink：{target_name}"))

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="Workspace root")
    args = parser.parse_args()
    root = args.root.resolve()
    issues = validate_store(root)
    if issues:
        print(f"FAIL: {len(issues)} issue(s)")
        for issue in issues:
            print(f"- {issue.render(root)}")
        return 1
    print("PASS: mechanism network store is structurally valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
