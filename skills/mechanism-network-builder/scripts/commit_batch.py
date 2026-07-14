#!/usr/bin/env python3
"""Commit a staged knowledge batch and roll it back if validation fails."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

from validate_store import configured_store, validate_store


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def staged_files(staging: Path, store_relative: Path) -> list[Path]:
    staged_store = staging / store_relative
    if not staged_store.is_dir():
        raise ValueError(f"staging 必须包含 {store_relative.as_posix()}/ 目录")
    files = sorted(path for path in staged_store.rglob("*") if path.is_file())
    if not files:
        raise ValueError(f"staging/{store_relative.as_posix()} 中没有待写入文件")
    return files


def commit(root: Path, staging: Path, fail_after: int | None = None) -> None:
    root = root.resolve()
    staging = staging.resolve()
    store, config_error = configured_store(root)
    if config_error:
        raise ValueError(config_error)
    store_relative = store.relative_to(root)
    files = staged_files(staging, store_relative)
    backups: dict[Path, bytes | None] = {}
    written: list[Path] = []

    try:
        for index, source in enumerate(files, start=1):
            relative = source.relative_to(staging / store_relative)
            target = (store / relative).resolve()
            if store not in target.parents:
                raise ValueError(f"非法目标路径：{relative}")

            backups[target] = target.read_bytes() if target.exists() else None
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                dir=target.parent, prefix=f".{target.name}.", suffix=".tmp", delete=False
            ) as handle:
                temporary = Path(handle.name)
                with source.open("rb") as reader:
                    shutil.copyfileobj(reader, handle)
            os.replace(temporary, target)
            written.append(target)

            if fail_after is not None and index >= fail_after:
                raise RuntimeError("模拟批量写入失败")

        issues = validate_store(root)
        if issues:
            rendered = "\n".join(f"- {issue.render(root)}" for issue in issues)
            raise RuntimeError(f"写入后校验失败：\n{rendered}")
    except Exception:
        for target in reversed(written):
            original = backups[target]
            if original is None:
                target.unlink(missing_ok=True)
            else:
                with tempfile.NamedTemporaryFile(
                    dir=target.parent, prefix=f".{target.name}.", suffix=".restore", delete=False
                ) as handle:
                    temporary = Path(handle.name)
                    handle.write(original)
                os.replace(temporary, target)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--staging", required=True, type=Path)
    parser.add_argument("--simulate-failure-after", type=int, help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        commit(args.root, args.staging, args.simulate_failure_after)
    except Exception as exc:
        print(f"ROLLBACK: {exc}")
        return 1
    print("PASS: batch committed and store validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
