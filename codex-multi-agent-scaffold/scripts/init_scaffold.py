#!/usr/bin/env python3
"""Initialize or update a project's Codex multi-agent scaffold."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


SKIP_NAMES = {".DS_Store", "__pycache__"}


@dataclass
class InitResult:
    target: str
    scaffold_source: str
    dry_run: bool
    force: bool
    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        return "failed" if self.errors else "ok"

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "target": self.target,
            "scaffold_source": self.scaffold_source,
            "dry_run": self.dry_run,
            "force": self.force,
            "created": self.created,
            "updated": self.updated,
            "skipped": self.skipped,
            "errors": self.errors,
        }


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def iter_scaffold_files(source: Path) -> Iterable[Path]:
    for path in sorted(source.rglob("*")):
        if path.name in SKIP_NAMES:
            continue
        yield path


def ensure_directory(path: Path, result: InitResult, target_root: Path) -> None:
    if path.exists() and not path.is_dir():
        result.errors.append(f"Target path exists but is not a directory: {rel(path, target_root)}")
        return
    if path.exists():
        result.skipped.append(rel(path, target_root))
        return
    result.created.append(rel(path, target_root))
    if not result.dry_run:
        path.mkdir(parents=True, exist_ok=True)


def copy_file(source: Path, dest: Path, result: InitResult, target_root: Path) -> None:
    dest_label = rel(dest, target_root)
    if dest.exists() and not result.force:
        result.skipped.append(dest_label)
        return

    if dest.exists() and result.force:
        result.updated.append(dest_label)
    else:
        result.created.append(dest_label)

    if result.dry_run:
        return

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)


def initialize_scaffold(target: Path, force: bool, dry_run: bool) -> InitResult:
    root = skill_root()
    source = root / "assets" / "scaffold"
    target = target.resolve()

    result = InitResult(
        target=target.as_posix(),
        scaffold_source=source.as_posix(),
        dry_run=dry_run,
        force=force,
    )

    if not source.is_dir():
        result.errors.append(f"Scaffold source not found: {source}")
        return result

    if not target.exists():
        result.errors.append(f"Target path does not exist: {target}")
        return result

    if not target.is_dir():
        result.errors.append(f"Target path is not a directory: {target}")
        return result

    for source_path in iter_scaffold_files(source):
        relative = source_path.relative_to(source)
        dest_path = target / relative

        if source_path.is_dir():
            ensure_directory(dest_path, result, target)
        elif source_path.is_file():
            copy_file(source_path, dest_path, result, target)

    return result


def render_markdown(result: InitResult) -> str:
    lines = [
        "# Init Scaffold Result",
        "",
        f"- Status: `{result.status}`",
        f"- Target: `{result.target}`",
        f"- Scaffold source: `{result.scaffold_source}`",
        f"- Dry run: `{str(result.dry_run).lower()}`",
        f"- Force: `{str(result.force).lower()}`",
        "",
    ]

    for title, values in (
        ("Created", result.created),
        ("Updated", result.updated),
        ("Skipped", result.skipped),
        ("Errors", result.errors),
    ):
        lines.append(f"## {title}")
        lines.append("")
        if values:
            lines.extend(f"- `{value}`" for value in values)
        else:
            lines.append("- None")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Initialize or update a target project's Codex multi-agent scaffold."
    )
    parser.add_argument(
        "--target",
        default=".",
        help="Target project directory. Defaults to the current directory.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing scaffold files. Defaults to preserving existing files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview created/updated/skipped files without writing changes.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format. Defaults to json.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    result = initialize_scaffold(
        target=Path(args.target),
        force=args.force,
        dry_run=args.dry_run,
    )

    if args.format == "markdown":
        print(render_markdown(result), end="")
    else:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))

    return 1 if result.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
