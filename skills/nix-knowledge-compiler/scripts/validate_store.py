#!/usr/bin/env python3
"""Deterministic validator for a nix-knowledge-compiler dual-layer store.

The validator intentionally supports only the small YAML subset used by the
canonical atom frontmatter contract.  It has no third-party dependencies.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass, field
import hashlib
from pathlib import Path
import re
import sys
from typing import Any, Iterable
from urllib.parse import urlsplit


FRONTMATTER_FIELDS = (
    "id",
    "status",
    "source",
    "tags",
    "aliases",
    "depends_on",
    "components",
)
LIST_FIELDS = {"source", "tags", "aliases", "depends_on", "components"}
STATUSES = {"draft", "stable", "deprecated", "merged"}

MECHANISM_SECTIONS = (
    "场景用途",
    "CLC方向",
    "定义",
    "边界",
    "机制核心",
    "参与角色",
    "成立条件",
    "迁移边界",
    "复用价值",
    "领域绑定",
    "脱域说明",
    "区分说明",
    "必要说明",
    "依赖",
    "组件",
)
LEGACY_SECTIONS = tuple(
    section
    for section in MECHANISM_SECTIONS
    if section not in {"机制核心", "参与角色", "成立条件", "迁移边界"}
)
NECESSARY_TOKENS = (
    "证据状态",
    "来源支持",
    "编译器推导",
    "待验证",
    "学术线索",
    "命名依据",
    "常见别名",
    "独立语义复核",
)
RECONSTRUCTION_FIELDS = ("source", "source_sha256")
RECONSTRUCTION_SECTIONS = (
    "核心结论",
    "论证链",
    "关键概念",
    "建议与适用范围",
    "证据与文本问题",
    "机制 atom 映射",
)
CLC_ROOT_CODES = frozenset("ABCDEFGHIJKNOPQRSTUVXZ")
BINDING_STATUSES = ("来源支持", "独立材料验证", "机制推演")
EVIDENCE_STATUSES = ("单一来源", "多源互证", "权威原理+应用验证", "证据不足")
STABLE_EVIDENCE_STATUSES = {"多源互证", "权威原理+应用验证"}
UNRESOLVED_MARKERS = (
    "待验证",
    "待核验",
    "未验证",
    "未核验",
    "待确认",
    "待补充",
    "TODO",
    "TBD",
)


def _load_classification_tags() -> frozenset[str]:
    """Load the canonical navigation vocabulary bundled with the skill."""
    path = Path(__file__).resolve().parent.parent / "references" / "classification.md"
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return frozenset()
    return frozenset(
        f"{code}/{name}"
        for code, name in re.findall(
            r"(?m)^- `([A-Z][A-Z]?(?:[0-9]+(?:\.[0-9]+)?)?)/([^`]+)`[ \t]*$",
            text,
        )
    )


CLASSIFICATION_TAGS = _load_classification_tags()

_FIELD_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:[ \t]*(.*))?$")
_LIST_ITEM_RE = re.compile(r"^[ \t]+-[ \t]*(.*)$")
_HEADING_RE = re.compile(r"(?m)^##[ \t]+(.+?)[ \t]*$")
_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]")
_WINDOWS_DRIVE_RE = re.compile(r"^([A-Za-z]):[\\/](.*)$")
_TABLE_SEPARATOR_RE = re.compile(r"^:?-{3,}:?$")
_RELATION_LINE_RE = re.compile(
    r"(?m)^\s*-\s*\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]\s*-\s*([A-Za-z_]+)\s*[：:]\s*(.+?)\s*$"
)
RELATION_TYPES = {
    "depends_on": {"prerequisite", "defined_by", "grounded_in"},
    "components": {"composed_of", "implements", "instantiates"},
}
SEMANTIC_REVIEW_STATUSES = {"通过", "未通过", "未执行"}


def _blank_preserving_newlines(value: str) -> str:
    return "".join("\n" if char == "\n" else "\r" if char == "\r" else " " for char in value)


def _mask_nonstructural(text: str) -> str:
    """Mask fenced code and HTML comments without changing string offsets."""
    masked = list(text)
    for match in re.finditer(r"<!--[\s\S]*?-->", text):
        replacement = _blank_preserving_newlines(match.group(0))
        masked[match.start() : match.end()] = replacement

    without_comments = "".join(masked)
    offset = 0
    fence_char: str | None = None
    fence_length = 0
    for line in without_comments.splitlines(keepends=True):
        fence_match = re.match(r"^[ \t]*(`{3,}|~{3,})", line)
        is_fence_line = False
        if fence_match:
            marker = fence_match.group(1)
            if fence_char is None:
                fence_char = marker[0]
                fence_length = len(marker)
                is_fence_line = True
            elif marker[0] == fence_char and len(marker) >= fence_length:
                is_fence_line = True
                fence_char = None
                fence_length = 0
        if fence_char is not None or is_fence_line:
            replacement = _blank_preserving_newlines(line)
            masked[offset : offset + len(line)] = replacement
        offset += len(line)
    return "".join(masked)


@dataclass(frozen=True, order=True)
class Issue:
    location: str
    code: str
    message: str

    def render(self, severity: str) -> str:
        return f"{severity} [{self.location}] {self.code}: {self.message}"


@dataclass
class ValidationResult:
    errors: list[Issue] = field(default_factory=list)
    warnings: list[Issue] = field(default_factory=list)
    atom_count: int = 0
    reconstruction_count: int = 0
    store_path: Path | None = None

    def error(self, location: str, code: str, message: str) -> None:
        self.errors.append(Issue(location, code, message))

    def warning(self, location: str, code: str, message: str) -> None:
        self.warnings.append(Issue(location, code, message))

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass
class AtomRecord:
    path: Path
    data: dict[str, Any]
    body: str

    @property
    def location(self) -> str:
        return self.path.name


def _clc_code(tag: str) -> str:
    return tag.split("/", 1)[0]


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return value[1:-1]
        return parsed
    return value


def _split_inline_list(value: str) -> list[Any] | None:
    value = value.strip()
    if not (value.startswith("[") and value.endswith("]")):
        return None
    inner = value[1:-1].strip()
    if not inner:
        return []
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        parsed = None
    if isinstance(parsed, list):
        return parsed

    items: list[str] = []
    current: list[str] = []
    quote: str | None = None
    escaped = False
    for char in inner:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\" and quote:
            current.append(char)
            escaped = True
        elif char in {"'", '"'}:
            current.append(char)
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
        elif char == "," and quote is None:
            items.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    items.append("".join(current).strip())
    return [_parse_scalar(item) for item in items]


def _parse_frontmatter(path: Path, result: ValidationResult) -> AtomRecord | None:
    location = path.name
    try:
        text = path.read_text(encoding="utf-8").lstrip("\ufeff")
    except (OSError, UnicodeError) as exc:
        result.error(location, "READ_ERROR", str(exc))
        return None

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        result.error(location, "FRONTMATTER_MISSING", "file must start with ---")
        return None
    try:
        closing = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration:
        result.error(location, "FRONTMATTER_UNCLOSED", "missing closing ---")
        return None

    data: dict[str, Any] = {}
    current_list: str | None = None
    for offset, line in enumerate(lines[1:closing], start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        field_match = _FIELD_RE.match(line)
        if field_match and not line[:1].isspace():
            key, raw_value = field_match.group(1), (field_match.group(2) or "")
            if key in data:
                result.error(location, "DUPLICATE_FIELD", f"frontmatter field {key!r} is duplicated")
                current_list = None
                continue
            if not raw_value.strip():
                data[key] = []
                current_list = key
            else:
                inline_list = _split_inline_list(raw_value)
                data[key] = inline_list if inline_list is not None else _parse_scalar(raw_value)
                current_list = None
            continue

        item_match = _LIST_ITEM_RE.match(line)
        if item_match and current_list is not None:
            data[current_list].append(_parse_scalar(item_match.group(1)))
            continue

        result.error(
            location,
            "FRONTMATTER_SYNTAX",
            f"unsupported frontmatter syntax at line {offset}: {line.strip()!r}",
        )
        current_list = None

    body = "\n".join(lines[closing + 1 :])
    return AtomRecord(path=path, data=data, body=body)


def _validate_string_list(
    record: AtomRecord,
    field_name: str,
    result: ValidationResult,
    minimum: int | None = None,
    maximum: int | None = None,
) -> list[str]:
    value = record.data.get(field_name)
    if not isinstance(value, list):
        result.error(record.location, "FIELD_TYPE", f"{field_name} must be a list")
        return []
    if minimum is not None and len(value) < minimum:
        result.error(record.location, "FIELD_CARDINALITY", f"{field_name} must contain at least {minimum} item(s)")
    if maximum is not None and len(value) > maximum:
        result.error(record.location, "FIELD_CARDINALITY", f"{field_name} must contain at most {maximum} item(s)")

    normalized: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            result.error(record.location, "LIST_ITEM_TYPE", f"{field_name}[{index}] must be a non-empty string")
            continue
        normalized.append(item.strip())
    duplicates = sorted({item for item in normalized if normalized.count(item) > 1})
    if duplicates:
        result.error(record.location, "DUPLICATE_LIST_ITEM", f"{field_name} contains duplicate item(s): {', '.join(duplicates)}")
    return normalized


def _is_http_url(value: str) -> bool:
    parsed = urlsplit(value)
    return parsed.scheme.lower() in {"http", "https"} and bool(parsed.netloc)


def _source_candidates(value: str, source_base: Path, atom_path: Path) -> list[Path]:
    drive_match = _WINDOWS_DRIVE_RE.match(value)
    if drive_match and sys.platform != "win32":
        drive, remainder = drive_match.groups()
        return [Path("/mnt") / drive.lower() / Path(remainder.replace("\\", "/"))]

    candidate = Path(value).expanduser()
    if candidate.is_absolute() or drive_match:
        return [candidate]
    return [source_base / candidate, atom_path.parent / candidate]


def _resolved_source_path(value: str, source_base: Path, atom_path: Path) -> Path | None:
    for candidate in _source_candidates(value, source_base, atom_path):
        try:
            if candidate.is_file():
                return candidate.resolve()
        except OSError:
            continue
    return None


def _section_contents(body: str) -> tuple[list[str], dict[str, str]]:
    matches = list(_HEADING_RE.finditer(_mask_nonstructural(body)))
    names = [match.group(1).strip() for match in matches]
    contents: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        name = match.group(1).strip()
        contents[name] = body[match.end() : end].strip()
    return names, contents


def _markdown_table(section: str) -> tuple[list[str], list[list[str]]] | None:
    visible = _mask_nonstructural(section)
    lines = [line.strip() for line in visible.splitlines() if line.strip().startswith("|") and line.strip().endswith("|")]
    if len(lines) < 3:
        return None

    def cells(line: str) -> list[str]:
        return [cell.strip().strip("`") for cell in line.strip("|").split("|")]

    header = cells(lines[0])
    separator = cells(lines[1])
    if len(header) != len(separator) or not all(_TABLE_SEPARATOR_RE.fullmatch(cell.replace(" ", "")) for cell in separator):
        return None
    rows = [cells(line) for line in lines[2:]]
    rows = [row for row in rows if len(row) == len(header)]
    return header, rows


def _binding_statuses(section: str) -> list[str]:
    table = _markdown_table(section)
    if table is None:
        return []
    header, rows = table
    try:
        index = header.index("验证状态")
    except ValueError:
        return []
    return [row[index] for row in rows if row[index]]


def _binding_evidence_rows(section: str) -> list[tuple[str, str]]:
    table = _markdown_table(section)
    if table is None:
        return []
    header, rows = table
    try:
        status_index = header.index("验证状态")
    except ValueError:
        return []
    evidence_index = next(
        (header.index(name) for name in ("证据定位", "来源") if name in header),
        None,
    )
    if evidence_index is None:
        return []
    return [
        (row[status_index], row[evidence_index])
        for row in rows
        if row[status_index] and row[evidence_index]
    ]


def _independent_binding_evidence(section: str) -> list[str]:
    return [
        evidence
        for status, evidence in _binding_evidence_rows(section)
        if status == "独立材料验证" and _is_substantive(evidence, minimum=4)
    ]


def _binding_source_identity(evidence: str, source_identities: dict[str, str]) -> str | None:
    normalized_evidence = evidence.replace("`", "").replace("\\", "/").strip().casefold()
    matches: set[str] = set()
    for source, identity in source_identities.items():
        normalized_source = source.replace("\\", "/").strip().casefold()
        basename = normalized_source.rstrip("/").rsplit("/", 1)[-1]
        for locator in {normalized_source, basename}:
            if not locator:
                continue
            if normalized_evidence == locator or any(
                normalized_evidence.startswith(locator + delimiter)
                for delimiter in (" ", "#", "；", ";", "：", "（", "(", "第")
            ):
                matches.add(identity)
    return next(iter(matches)) if len(matches) == 1 else None


def _label_values(section: str, label: str) -> list[str]:
    plain = _mask_nonstructural(section).replace("**", "").replace("`", "")
    matches = re.finditer(rf"(?m)^\s*(?:[-*]\s*)?{re.escape(label)}\s*[：:]\s*(.*?)\s*$", plain)
    return [match.group(1).strip().strip("。.;； ") for match in matches]


def _label_value(section: str, label: str) -> str | None:
    values = _label_values(section, label)
    return values[0] if len(values) == 1 else None


def _leading_status(value: str | None, allowed: Iterable[str]) -> str | None:
    if value is None:
        return None
    for status in allowed:
        if value == status or value.startswith(status + "；") or value.startswith(status + ";"):
            return status
    return None


def _semantic_review_status(value: str | None) -> str | None:
    if value is None:
        return None
    patterns = (
        ("通过", r"^通过；范围：(.+)$"),
        ("未通过", r"^未通过；原因：(.+)$"),
        ("未执行", r"^未执行；原因：(.+)$"),
    )
    for status, pattern in patterns:
        match = re.fullmatch(pattern, value)
        if not match:
            continue
        detail = match.group(1).strip()
        if not _is_substantive(detail, minimum=4) or "..." in detail or "…" in detail:
            return None
        if any(other in detail for other in SEMANTIC_REVIEW_STATUSES):
            return None
        return status
    return None


def _alias_values(section: str) -> set[str] | None:
    value = _label_value(section, "常见别名")
    if value is None:
        return None
    items = re.split(r"[、,，;；]", value)
    normalized = {
        item.strip().strip("`'\"“”‘’[]【】 ")
        for item in items
        if item.strip().strip("`'\"“”‘’[]【】 ")
    }
    return normalized


def _relation_entries(section: str) -> list[tuple[str, str, str]]:
    return [
        (match.group(1).strip(), match.group(2).strip(), match.group(3).strip())
        for match in _RELATION_LINE_RE.finditer(_mask_nonstructural(section))
    ]


def _is_substantive(value: str, minimum: int = 8) -> bool:
    compact = re.sub(r"[`#>*_|\-\s。，、：:；;（）()<>]", "", value)
    if compact in {"", "无", "暂无", "不适用", "待补充", "待验证", "TODO", "TBD"}:
        return False
    if "<" in value and ">" in value:
        return False
    return len(compact) >= minimum


def _wikilink_targets(section: str) -> set[str]:
    visible = _mask_nonstructural(section)
    return {match.group(1).strip() for match in _WIKILINK_RE.finditer(visible) if match.group(1).strip()}


def _unresolved_markers(body: str) -> list[str]:
    allowed_line = re.compile(r"^(?:[-*][ \t]+)?待验证[：:]无[。.]?$")
    unresolved: set[str] = set()
    for line in _mask_nonstructural(body).splitlines():
        stripped = line.strip()
        plain = stripped.replace("**", "").replace("`", "").replace(" ", "")
        if allowed_line.fullmatch(plain):
            check_line = plain.replace("待验证", "")
        else:
            check_line = stripped
        for marker in UNRESOLVED_MARKERS:
            if marker in check_line:
                unresolved.add(marker)
    return sorted(unresolved)


def _validate_body(record: AtomRecord, result: ValidationResult) -> None:
    names, contents = _section_contents(record.body)
    status = record.data.get("status")

    # Section keys are a machine interface and remain Chinese for every source
    # language. IDs, titles, aliases, and prose follow the source language.
    if isinstance(status, str) and status in {"deprecated", "merged"}:
        if tuple(names) == LEGACY_SECTIONS:
            result.warning(
                record.location,
                "LEGACY_SECTIONS",
                "deprecated/merged legacy atom omits the four mechanism sections",
            )
        elif tuple(names) != MECHANISM_SECTIONS:
            result.error(
                record.location,
                "SECTION_ORDER",
                "deprecated/merged atom must use all 15 sections or the canonical 11-section legacy form",
            )
    elif tuple(names) != MECHANISM_SECTIONS:
        result.error(
            record.location,
            "SECTION_ORDER",
            "atom sections must exactly match the canonical 15-section Chinese machine-key order",
        )

    necessary = contents.get("必要说明", "")
    invalid_labels = [
        token
        for token in NECESSARY_TOKENS
        if len(_label_values(necessary, token)) != 1 or not _label_values(necessary, token)[0]
    ]
    if invalid_labels:
        result.error(
            record.location,
            "NECESSARY_CONTENT",
            f"必要说明 must contain each required label exactly once with a non-empty value: {', '.join(invalid_labels)}",
        )

    evidence_status = _leading_status(_label_value(necessary, "证据状态"), EVIDENCE_STATUSES)
    if evidence_status is None:
        result.error(
            record.location,
            "EVIDENCE_STATUS",
            "证据状态 must start with exactly one canonical value",
        )
    elif status == "stable" and evidence_status not in STABLE_EVIDENCE_STATUSES:
        result.error(
            record.location,
            "STABLE_EVIDENCE",
            "stable atom must use 多源互证 or 权威原理+应用验证 as 证据状态",
        )

    semantic_review = _semantic_review_status(_label_value(necessary, "独立语义复核"))
    if semantic_review is None:
        result.error(
            record.location,
            "SEMANTIC_REVIEW",
            "独立语义复核 must be 通过；范围：具体内容, 未通过；原因：具体内容, or 未执行；原因：具体内容",
        )
    elif status == "stable" and semantic_review != "通过":
        result.error(record.location, "STABLE_EVIDENCE", "stable atom requires 独立语义复核：通过")

    if status == "stable":
        source_support = _label_value(necessary, "来源支持") or ""
        if not _is_substantive(source_support, minimum=4) or source_support.strip() == "无":
            result.error(record.location, "STABLE_EVIDENCE", "stable atom requires substantive 来源支持")
        if _label_value(necessary, "待验证") != "无":
            result.error(record.location, "STABLE_UNRESOLVED", "stable atom requires exactly 待验证：无")

    aliases = record.data.get("aliases")
    expected_aliases = {item.strip() for item in aliases if isinstance(item, str)} if isinstance(aliases, list) else set()
    actual_aliases = _alias_values(necessary)
    if actual_aliases is None or actual_aliases != expected_aliases:
        result.error(
            record.location,
            "ALIAS_MISMATCH",
            "必要说明/常见别名 must exactly match frontmatter aliases",
        )

    clc_section = contents.get("CLC方向", "")
    if "CLC全表扫描" not in clc_section or "22" not in clc_section or "主类" not in clc_section:
        result.error(
            record.location,
            "CLC_SCAN",
            "CLC方向 must record CLC全表扫描 of all 22 basic classes and a 主类 line",
        )
    tags = record.data.get("tags")
    expected_clc_tags = [item.strip() for item in tags if isinstance(item, str)] if isinstance(tags, list) else []
    missing_clc_tags = [tag for tag in expected_clc_tags if tag not in clc_section]
    if missing_clc_tags:
        result.error(
            record.location,
            "CLC_BODY_MISMATCH",
            f"CLC方向/主类 must include every frontmatter tag exactly as written: {', '.join(missing_clc_tags)}",
        )

    binding = contents.get("领域绑定", "")
    binding_statuses = _binding_statuses(binding)
    if not binding_statuses:
        result.error(
            record.location,
            "BINDING_STATUS",
            "领域绑定 must contain a Markdown table with a 验证状态 column and at least one data row",
        )
    invalid_binding_statuses = sorted({value for value in binding_statuses if value not in BINDING_STATUSES})
    if invalid_binding_statuses:
        result.error(
            record.location,
            "BINDING_STATUS",
            f"invalid domain-binding validation status: {', '.join(invalid_binding_statuses)}",
        )
    independent_evidence = _independent_binding_evidence(binding)
    if status == "stable" and not independent_evidence:
        result.error(
            record.location,
            "STABLE_EVIDENCE",
            "stable atom needs an 独立材料验证 table row with a non-empty 证据定位/来源 cell",
        )

    if status not in {"deprecated", "merged"}:
        for section_name in MECHANISM_SECTIONS[:-2]:
            minimum = 4 if section_name == "成立条件" else 8
            section_value = contents.get(section_name, "")
            visible_value = section_value if section_name == "机制核心" else _mask_nonstructural(section_value)
            if section_name in contents and not _is_substantive(visible_value, minimum=minimum):
                result.error(
                    record.location,
                    "SECTION_CONTENT",
                    f"## {section_name} must contain substantive, non-placeholder content",
                )

        mechanism = contents.get("机制核心", "")
        signature_match = re.search(r"函数签名\s*[：:]\s*([^\n]+)", mechanism)
        signature = signature_match.group(1).strip() if signature_match else ""
        if (
            not signature_match
            or len(re.findall(r"->|→", signature)) < 2
            or not _is_substantive(signature, minimum=6)
        ):
            result.error(
                record.location,
                "MECHANISM_SIGNATURE",
                "机制核心 must contain a non-placeholder 函数签名：输入 -> 操作 -> 输出",
            )
        missing_chain_tokens = [token for token in ("触发", "中介机制", "可观察结果", "适用边界") if token not in mechanism]
        if missing_chain_tokens or len(re.findall(r"->|→", mechanism)) < 5:
            result.error(
                record.location,
                "MECHANISM_CHAIN",
                "机制核心 must contain an arrow-linked 触发条件 -> 中介机制 -> 可观察结果 -> 适用边界 chain",
            )

        roles_table = _markdown_table(contents.get("参与角色", ""))
        valid_role_row = bool(
            roles_table
            and "角色" in roles_table[0]
            and any(all(_is_substantive(cell, minimum=2) for cell in row) for row in roles_table[1])
        )
        if not valid_role_row:
            result.error(
                record.location,
                "ROLE_TABLE",
                "参与角色 must contain a Markdown table with a 角色 column and a substantive data row",
            )

        conditions = contents.get("成立条件", "")
        if not re.search(r"(?m)^\s*(?:[-*]|\d+[.)])\s+\S", conditions):
            result.error(record.location, "CONDITION_FORMAT", "成立条件 must contain at least one checkable list item")

        migration = contents.get("迁移边界", "")
        missing_migration = [
            label
            for label, pattern in (
                ("可迁移到/可迁移结构", r"可迁移(?:到|结构)"),
                ("不能迁移到", r"不能迁移到"),
                ("假迁移警惕", r"假迁移警惕"),
            )
            if not re.search(pattern, migration)
        ]
        if missing_migration:
            result.error(
                record.location,
                "MIGRATION_BOUNDARY",
                f"迁移边界 missing required item(s): {', '.join(missing_migration)}",
            )

        if "调用方式" not in contents.get("复用价值", ""):
            result.error(record.location, "REUSE_CALL", "复用价值 must contain 调用方式")

    if status in {"deprecated", "merged"}:
        destination = _label_value(necessary, "去向")
        migration_reason = _label_value(necessary, "迁移理由")
        if not destination:
            result.error(record.location, "LIFECYCLE_TRACE", "deprecated/merged atom requires 去向")
        if not migration_reason or not _is_substantive(migration_reason, minimum=4):
            result.error(record.location, "LIFECYCLE_TRACE", "deprecated/merged atom requires a substantive 迁移理由")

    for field_name, section_name in (("depends_on", "依赖"), ("components", "组件")):
        expected_raw = record.data.get(field_name)
        expected = {item.strip() for item in expected_raw if isinstance(item, str)} if isinstance(expected_raw, list) else set()
        if section_name not in contents:
            result.error(record.location, "BODY_SECTION_MISSING", f"missing ## {section_name} section")
            continue
        actual = _wikilink_targets(contents[section_name])
        if expected != actual:
            missing = sorted(expected - actual)
            extra = sorted(actual - expected)
            details: list[str] = []
            if missing:
                details.append(f"missing body link(s): {', '.join(missing)}")
            if extra:
                details.append(f"extra body link(s): {', '.join(extra)}")
            result.error(record.location, "BODY_LINK_MISMATCH", f"{field_name}/## {section_name} mismatch; {'; '.join(details)}")

        entries = _relation_entries(contents[section_name])
        entry_targets = [target for target, _relation, _reason in entries]
        if set(entry_targets) != actual or len(entry_targets) != len(set(entry_targets)):
            result.error(
                record.location,
                "RELATION_FORMAT",
                f"## {section_name} links must each use [[id]] - relation_type：non-empty reason exactly once",
            )
        for target, relation, reason in entries:
            if relation not in RELATION_TYPES[field_name]:
                allowed = ", ".join(sorted(RELATION_TYPES[field_name]))
                result.error(
                    record.location,
                    "RELATION_TYPE",
                    f"{field_name} relation for {target} must be one of: {allowed}",
                )
            if not _is_substantive(reason, minimum=4):
                result.error(record.location, "RELATION_REASON", f"relation for {target} requires a substantive reason")

    unresolved = _unresolved_markers(record.body)
    if status == "stable" and unresolved:
        result.error(
            record.location,
            "STABLE_UNRESOLVED",
            f"stable atom contains unresolved marker(s): {', '.join(unresolved)}",
        )
    elif status == "draft" and unresolved:
        result.warning(
            record.location,
            "DRAFT_UNRESOLVED",
            f"draft atom contains unresolved marker(s): {', '.join(unresolved)}",
        )


def _validate_record(record: AtomRecord, source_base: Path, result: ValidationResult) -> None:
    actual_fields = set(record.data)
    expected_fields = set(FRONTMATTER_FIELDS)
    missing = [field_name for field_name in FRONTMATTER_FIELDS if field_name not in actual_fields]
    extra = sorted(actual_fields - expected_fields)
    if missing:
        result.error(record.location, "MISSING_FIELD", f"missing field(s): {', '.join(missing)}")
    if extra:
        result.error(record.location, "EXTRA_FIELD", f"unexpected field(s): {', '.join(extra)}")

    atom_id = record.data.get("id")
    if not isinstance(atom_id, str) or not atom_id.strip():
        result.error(record.location, "ID_INVALID", "id must be a non-empty string")
    elif record.path.name != f"{atom_id.strip()}.md":
        result.error(record.location, "FILENAME_MISMATCH", f"filename must be {atom_id.strip()}.md")

    status = record.data.get("status")
    if not isinstance(status, str) or status not in STATUSES:
        result.error(record.location, "STATUS_INVALID", f"status must be one of: {', '.join(sorted(STATUSES))}")

    sources = _validate_string_list(record, "source", result, minimum=1)
    tags = _validate_string_list(record, "tags", result, minimum=1, maximum=3)
    _validate_string_list(record, "aliases", result, minimum=2, maximum=6)
    _validate_string_list(record, "depends_on", result)
    _validate_string_list(record, "components", result)

    local_source_identities: set[str] = set()
    local_source_hashes: set[str] = set()
    source_identities: dict[str, str] = {}
    for source in sources:
        if _is_http_url(source):
            result.warning(record.location, "SOURCE_URL_UNVERIFIED", f"URL source was not fetched: {source}")
            parsed = urlsplit(source)
            source_identities[source] = f"url:{parsed.scheme.casefold()}://{parsed.netloc.casefold()}{parsed.path}?{parsed.query}".rstrip("?")
        elif source.lower().startswith(("http:", "https:")):
            result.error(record.location, "SOURCE_INVALID_URL", f"invalid HTTP(S) URL: {source}")
        else:
            resolved_source = _resolved_source_path(source, source_base, record.path)
            if resolved_source is None:
                result.error(record.location, "SOURCE_NOT_FOUND", f"source file does not exist: {source}")
            else:
                identity = str(resolved_source)
                if sys.platform == "win32" or re.match(r"^/mnt/[A-Za-z]/", identity):
                    identity = identity.casefold()
                local_source_identities.add(identity)
                source_identities[source] = f"file:{identity}"
                try:
                    local_source_hashes.add(hashlib.sha256(resolved_source.read_bytes()).hexdigest())
                except OSError as exc:
                    result.error(record.location, "SOURCE_READ_ERROR", f"cannot hash source file {source}: {exc}")

    for tag in tags:
        if tag not in CLASSIFICATION_TAGS:
            result.error(record.location, "TAG_NOT_ALLOWED", f"tag is not in the bundled classification: {tag}")
        elif "/" not in tag or not re.fullmatch(r"[A-Z][A-Z]?(?:[0-9]+(?:\.[0-9]+)?)?", _clc_code(tag)):
            result.error(record.location, "TAG_NOT_CLC", f"tag must use CODE/CLC official-name form: {tag}")

    if status == "stable":
        if len(local_source_identities) < 2:
            result.error(
                record.location,
                "STABLE_EVIDENCE",
                "stable atom must cite at least two distinct, locally resolvable source files",
            )
        if len(local_source_hashes) < 2:
            result.error(
                record.location,
                "STABLE_EVIDENCE",
                "stable atom must cite at least two source files with distinct content hashes",
            )
        _names, contents = _section_contents(record.body)
        binding = contents.get("领域绑定", "")
        binding_statuses = _binding_statuses(binding)
        if "独立材料验证" not in binding_statuses:
            result.error(
                record.location,
                "STABLE_EVIDENCE",
                "stable atom must contain at least one 独立材料验证 domain binding",
            )
        evidence_rows = _binding_evidence_rows(binding)
        support_identities = {
            identity
            for row_status, evidence in evidence_rows
            if row_status == "来源支持"
            for identity in [_binding_source_identity(evidence, source_identities)]
            if identity is not None
        }
        independent_identities = {
            identity
            for row_status, evidence in evidence_rows
            if row_status == "独立材料验证"
            for identity in [_binding_source_identity(evidence, source_identities)]
            if identity is not None
        }
        if not support_identities or not independent_identities:
            result.error(
                record.location,
                "STABLE_EVIDENCE",
                "stable atom requires source-supported and independently validated rows that resolve to frontmatter sources",
            )
        elif not any(support != independent for support in support_identities for independent in independent_identities):
            result.error(
                record.location,
                "STABLE_EVIDENCE",
                "来源支持 and 独立材料验证 rows must resolve to different source identities",
            )

    _names, contents = _section_contents(record.body)
    for row_status, evidence in _binding_evidence_rows(contents.get("领域绑定", "")):
        if row_status in {"来源支持", "独立材料验证"} and _binding_source_identity(evidence, source_identities) is None:
            result.error(
                record.location,
                "BINDING_EVIDENCE",
                f"{row_status} evidence must start with an exact frontmatter source locator or its unambiguous basename: {evidence}",
            )

    _validate_body(record, result)


def _canonical_cycle(nodes: list[str]) -> tuple[str, ...]:
    if nodes and nodes[0] == nodes[-1]:
        nodes = nodes[:-1]
    rotations = [tuple(nodes[index:] + nodes[:index]) for index in range(len(nodes))]
    return min(rotations) if rotations else tuple()


def _find_cycles(adjacency: dict[str, set[str]]) -> list[tuple[str, ...]]:
    color = {node: 0 for node in adjacency}
    stack: list[str] = []
    stack_index: dict[str, int] = {}
    cycles: set[tuple[str, ...]] = set()

    def visit(node: str) -> None:
        color[node] = 1
        stack_index[node] = len(stack)
        stack.append(node)
        for target in sorted(adjacency[node]):
            if target == node or target not in adjacency:
                continue
            if color[target] == 0:
                visit(target)
            elif color[target] == 1:
                cycles.add(_canonical_cycle(stack[stack_index[target] :] + [target]))
        stack.pop()
        stack_index.pop(node, None)
        color[node] = 2

    for node in sorted(adjacency):
        if color[node] == 0:
            visit(node)
    return sorted(cycles)


def _validate_graph(records: Iterable[AtomRecord], result: ValidationResult) -> None:
    records = list(records)
    by_id: dict[str, list[AtomRecord]] = {}
    for record in records:
        atom_id = record.data.get("id")
        if isinstance(atom_id, str) and atom_id.strip():
            by_id.setdefault(atom_id.strip(), []).append(record)

    for atom_id, duplicates in sorted(by_id.items()):
        if len(duplicates) > 1:
            locations = ", ".join(sorted(record.location for record in duplicates))
            result.error("<store>", "DUPLICATE_ID", f"id {atom_id!r} appears in: {locations}")

    known_ids = set(by_id)
    adjacency: dict[str, set[str]] = {atom_id: set() for atom_id in known_ids}
    lifecycle_adjacency: dict[str, set[str]] = {atom_id: set() for atom_id in known_ids}
    statuses = {atom_id: by_id[atom_id][0].data.get("status") for atom_id in known_ids}
    for atom_id in sorted(known_ids):
        record = by_id[atom_id][0]
        status = record.data.get("status")
        if status in {"deprecated", "merged"}:
            _names, contents = _section_contents(record.body)
            destination = _label_value(contents.get("必要说明", ""), "去向") or ""
            destination_links = _wikilink_targets(destination)
            if status == "merged" and len(destination_links) != 1:
                result.error(
                    record.location,
                    "LIFECYCLE_TARGET",
                    "merged atom must have exactly one 去向 wikilink",
                )
            for target in sorted(destination_links):
                if target == atom_id:
                    result.error(record.location, "LIFECYCLE_TARGET", "lifecycle destination cannot reference itself")
                elif target not in known_ids:
                    result.error(record.location, "LIFECYCLE_TARGET", f"lifecycle destination does not exist: {target}")
                elif status == "merged":
                    lifecycle_adjacency[atom_id].add(target)

        for field_name in ("depends_on", "components"):
            raw_targets = record.data.get(field_name)
            if not isinstance(raw_targets, list):
                continue
            for raw_target in raw_targets:
                if not isinstance(raw_target, str) or not raw_target.strip():
                    continue
                target = raw_target.strip()
                if target == atom_id:
                    result.error(record.location, "SELF_LOOP", f"{field_name} contains self-reference {target!r}")
                    continue
                if target not in known_ids:
                    result.error(record.location, "MISSING_TARGET", f"{field_name} target does not exist: {target}")
                    continue
                adjacency[atom_id].add(target)

    for cycle in _find_cycles(adjacency):
        rendered = " -> ".join((*cycle, cycle[0]))
        result.error("<graph>", "GRAPH_CYCLE", f"depends_on/components union contains cycle: {rendered}")

    for cycle in _find_cycles(lifecycle_adjacency):
        rendered = " -> ".join((*cycle, cycle[0]))
        result.error("<lifecycle>", "LIFECYCLE_CYCLE", f"merged destination chain contains cycle: {rendered}")

    for start in sorted(atom_id for atom_id, status in statuses.items() if status == "merged"):
        current = start
        seen: set[str] = set()
        while statuses.get(current) == "merged" and current not in seen:
            seen.add(current)
            targets = lifecycle_adjacency.get(current, set())
            if len(targets) != 1:
                break
            current = next(iter(targets))
        if current in seen:
            continue
        if statuses.get(current) not in {"draft", "stable"}:
            result.error(
                by_id[start][0].location,
                "LIFECYCLE_TARGET",
                "merged destination chain must terminate at a draft or stable atom",
            )


def _validate_reconstructions(
    reconstruction_dir: Path,
    source_base: Path,
    atom_records: list[AtomRecord],
    result: ValidationResult,
) -> None:
    if not reconstruction_dir.is_dir():
        result.error(
            "<reconstructions>",
            "RECONSTRUCTION_STORE_MISSING",
            "workspace root must contain reconstructions/ for source-level meaning preservation",
        )
        return

    atoms_by_id = {
        record.data.get("id"): record
        for record in atom_records
        if isinstance(record.data.get("id"), str)
    }
    seen_sources: dict[str, str] = {}
    reconstruction_paths = sorted(
        path for path in reconstruction_dir.glob("*.md") if path.name.casefold() != "readme.md"
    )
    for path in reconstruction_paths:
        record = _parse_frontmatter(path, result)
        if record is None:
            continue
        result.reconstruction_count += 1
        actual_fields = set(record.data)
        expected_fields = set(RECONSTRUCTION_FIELDS)
        missing = [name for name in RECONSTRUCTION_FIELDS if name not in actual_fields]
        extra = sorted(actual_fields - expected_fields)
        if missing:
            result.error(record.location, "RECONSTRUCTION_FIELD", f"missing field(s): {', '.join(missing)}")
        if extra:
            result.error(record.location, "RECONSTRUCTION_FIELD", f"unexpected field(s): {', '.join(extra)}")

        source = record.data.get("source")
        source_hash = record.data.get("source_sha256")
        resolved_source: Path | None = None
        if not isinstance(source, str) or not source.strip() or _is_http_url(source):
            result.error(record.location, "RECONSTRUCTION_SOURCE", "source must be one locally resolvable path")
        else:
            resolved_source = _resolved_source_path(source, source_base, record.path)
            if resolved_source is None:
                result.error(record.location, "RECONSTRUCTION_SOURCE", f"source file does not exist: {source}")
            else:
                identity = str(resolved_source).casefold() if sys.platform == "win32" else str(resolved_source)
                prior = seen_sources.get(identity)
                if prior is not None:
                    result.error(
                        record.location,
                        "RECONSTRUCTION_DUPLICATE_SOURCE",
                        f"source already has an active reconstruction: {prior}",
                    )
                else:
                    seen_sources[identity] = record.location
        if not isinstance(source_hash, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", source_hash.strip()):
            result.error(record.location, "RECONSTRUCTION_HASH", "source_sha256 must be a full hexadecimal SHA-256")
        elif resolved_source is not None:
            try:
                actual_hash = hashlib.sha256(resolved_source.read_bytes()).hexdigest()
            except OSError as exc:
                result.error(record.location, "RECONSTRUCTION_HASH", f"cannot hash source: {exc}")
            else:
                if actual_hash.casefold() != source_hash.strip().casefold():
                    result.error(record.location, "RECONSTRUCTION_STALE", "source_sha256 no longer matches source bytes")

        names, contents = _section_contents(record.body)
        if tuple(names) != RECONSTRUCTION_SECTIONS:
            result.error(
                record.location,
                "RECONSTRUCTION_SECTIONS",
                "reconstruction sections must exactly match the canonical six-section order",
            )
        for section_name in RECONSTRUCTION_SECTIONS:
            if not _is_substantive(_mask_nonstructural(contents.get(section_name, "")), minimum=12):
                result.error(
                    record.location,
                    "RECONSTRUCTION_CONTENT",
                    f"## {section_name} must contain substantive content",
                )

        review = _label_value(contents.get("证据与文本问题", ""), "原文替代验收")
        if _semantic_review_status(review) is None:
            result.error(
                record.location,
                "RECONSTRUCTION_REVIEW",
                "原文替代验收 must be 通过；范围：..., 未通过；原因：..., or 未执行；原因：...",
            )

        mapping = contents.get("机制 atom 映射", "")
        for target in sorted(_wikilink_targets(mapping)):
            atom = atoms_by_id.get(target)
            if atom is None:
                result.error(record.location, "RECONSTRUCTION_LINK", f"mapped atom does not exist: {target}")
                continue
            atom_sources = atom.data.get("source")
            if isinstance(source, str) and isinstance(atom_sources, list) and source not in atom_sources:
                result.error(
                    record.location,
                    "RECONSTRUCTION_SOURCE_LINK",
                    f"mapped atom {target} does not cite the reconstruction source",
                )


def validate_store(path: str | Path) -> ValidationResult:
    requested = Path(path).expanduser().resolve()
    result = ValidationResult()
    if not CLASSIFICATION_TAGS:
        result.error(
            "<validator>",
            "CLASSIFICATION_UNAVAILABLE",
            "bundled references/classification.md is missing or contains no tags",
        )
    available_roots = {_clc_code(tag) for tag in CLASSIFICATION_TAGS if _clc_code(tag) in CLC_ROOT_CODES}
    missing_roots = sorted(CLC_ROOT_CODES - available_roots)
    if missing_roots:
        result.error(
            "<validator>",
            "CLC_INCOMPLETE",
            f"classification registry must cover all 22 basic classes; missing: {', '.join(missing_roots)}",
        )
    if not requested.exists() or not requested.is_dir():
        result.error(str(requested), "STORE_NOT_FOUND", "validation path must be an existing directory")
        return result

    if (requested / "atoms").is_dir():
        store_path = requested / "atoms"
        source_base = requested
    else:
        store_path = requested
        source_base = requested.parent
    result.store_path = store_path

    atom_paths = sorted(
        path for path in store_path.glob("*.md") if path.name.casefold() != "readme.md"
    )
    records: list[AtomRecord] = []
    for atom_path in atom_paths:
        record = _parse_frontmatter(atom_path, result)
        if record is not None:
            records.append(record)
            _validate_record(record, source_base, result)

    result.atom_count = len(records)
    _validate_graph(records, result)
    if (requested / "atoms").is_dir():
        _validate_reconstructions(requested / "reconstructions", source_base, records, result)
    result.errors.sort()
    result.warnings.sort()
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a canonical mechanism atom store.")
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="workspace root containing atoms/, or the atoms directory itself",
    )
    parser.add_argument(
        "--root",
        dest="root",
        help="explicit workspace root containing atoms/ (preferred for autonomous runs)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.path is not None and args.root is not None:
        print("ERROR [<cli>] ARGUMENT_CONFLICT: use either positional path or --root, not both")
        return 2
    target = args.root or args.path or "."
    result = validate_store(target)
    for issue in result.errors:
        print(issue.render("ERROR"))
    for issue in result.warnings:
        print(issue.render("WARNING"))
    store = str(result.store_path) if result.store_path is not None else str(Path(target).resolve())
    print(
        f"Validated {result.atom_count} atom(s) and {result.reconstruction_count} reconstruction(s) in {store}: "
        f"{len(result.errors)} error(s), {len(result.warnings)} warning(s)."
    )
    return 1 if result.errors else 0


if __name__ == "__main__":
    sys.exit(main())
