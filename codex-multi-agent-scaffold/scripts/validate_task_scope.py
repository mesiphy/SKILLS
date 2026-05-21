#!/usr/bin/env python3
"""Validate that modified files stay within a task's allowed scope."""

from __future__ import annotations

import argparse
import fnmatch
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ScopeResult:
    status: str
    target: str
    task: str
    base: str
    allowed_scope: list[str]
    modified_files: list[str]
    out_of_scope: list[str]
    warnings: list[str]
    errors: list[str]


def rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def extract_allowed_scope(task_file: Path) -> list[str]:
    text = read_text(task_file)
    if not text:
        return []

    lines = text.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        normalized = line.lower()
        if line.startswith("## ") and (
            "allowed scope" in normalized or "允许修改范围" in line
        ):
            start = index + 1
            break

    if start is None:
        return []

    items: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        stripped = line.strip()
        if not stripped.startswith(("-", "*")):
            continue
        value = stripped[1:].strip()
        value = value.strip("`").strip()
        if not value or value.upper() in {"TODO", "UNKNOWN"}:
            continue
        items.append(value)

    return items


def git_modified_files(target: Path, base: str) -> tuple[list[str], list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []

    inside = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        warnings.append("Target is not a git repository; task scope diff check cannot run.")
        return [], warnings, errors

    command = ["git", "diff", "--name-only", base]
    diff = subprocess.run(
        command,
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if diff.returncode != 0:
        errors.append(f"Failed to run {' '.join(command)}: {diff.stderr.strip()}")
        return [], warnings, errors

    files = [line.strip() for line in diff.stdout.splitlines() if line.strip()]
    return sorted(files), warnings, errors


def is_allowed(file_path: str, allowed_scope: list[str]) -> bool:
    if not allowed_scope:
        return False

    normalized_file = file_path.strip("/")
    for raw_pattern in allowed_scope:
        pattern = normalize_scope_pattern(raw_pattern)
        if not pattern:
            continue
        if pattern in {".", "./", "**"}:
            return True
        if pattern.endswith("/**"):
            prefix = pattern[:-3].rstrip("/")
            if normalized_file == prefix or normalized_file.startswith(prefix + "/"):
                return True
        elif pattern.endswith("/"):
            prefix = pattern.rstrip("/")
            if normalized_file == prefix or normalized_file.startswith(prefix + "/"):
                return True
        elif any(char in pattern for char in "*?[]"):
            if fnmatch.fnmatch(normalized_file, pattern):
                return True
        elif normalized_file == pattern or normalized_file.startswith(pattern.rstrip("/") + "/"):
            return True

    return False


def normalize_scope_pattern(value: str) -> str:
    value = value.strip()
    if not value:
        return ""

    # Strip common explanatory suffixes after a Chinese or ASCII comma.
    for separator in ("，", ","):
        if separator in value:
            value = value.split(separator, 1)[0].strip()

    # Keep the first inline-code path if present.
    if "`" in value:
        parts = [part.strip() for part in value.split("`")]
        code_parts = [part for index, part in enumerate(parts) if index % 2 == 1 and part]
        if code_parts:
            value = code_parts[0]

    value = value.removeprefix("./")
    return value.strip("/")


def validate_scope(target: Path, task: Path, base: str) -> ScopeResult:
    target = target.resolve()
    task_path = task if task.is_absolute() else target / task
    warnings: list[str] = []
    errors: list[str] = []

    if not target.exists() or not target.is_dir():
        errors.append(f"Target path is not a directory: {target}")

    if not task_path.exists() or not task_path.is_file():
        errors.append(f"Task file does not exist: {task_path}")
        allowed_scope: list[str] = []
    else:
        allowed_scope = extract_allowed_scope(task_path)
        if not allowed_scope:
            errors.append("Allowed Scope section is missing or empty.")

    if errors:
        return ScopeResult(
            status="FAIL",
            target=target.as_posix(),
            task=task_path.as_posix(),
            base=base,
            allowed_scope=allowed_scope,
            modified_files=[],
            out_of_scope=[],
            warnings=warnings,
            errors=errors,
        )

    modified_files, git_warnings, git_errors = git_modified_files(target, base)
    warnings.extend(git_warnings)
    errors.extend(git_errors)

    out_of_scope = [
        file_path
        for file_path in modified_files
        if not is_allowed(file_path, allowed_scope)
    ]

    if errors or out_of_scope:
        status = "FAIL"
    elif warnings:
        status = "WARN"
    else:
        status = "PASS"

    return ScopeResult(
        status=status,
        target=target.as_posix(),
        task=task_path.as_posix(),
        base=base,
        allowed_scope=allowed_scope,
        modified_files=modified_files,
        out_of_scope=out_of_scope,
        warnings=warnings,
        errors=errors,
    )


def render_report(result: ScopeResult) -> str:
    lines = [
        "# Task Scope Validation Report",
        "",
        f"- Status: `{result.status}`",
        f"- Target: `{result.target}`",
        f"- Task: `{result.task}`",
        f"- Base: `{result.base}`",
        "",
        "## Allowed Scope",
        "",
    ]

    lines.extend(f"- `{item}`" for item in result.allowed_scope) if result.allowed_scope else lines.append("- None")

    lines.extend(["", "## Modified Files", ""])
    lines.extend(f"- `{item}`" for item in result.modified_files) if result.modified_files else lines.append("- None")

    lines.extend(["", "## Out Of Scope Files", ""])
    lines.extend(f"- `{item}`" for item in result.out_of_scope) if result.out_of_scope else lines.append("- None")

    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in result.warnings) if result.warnings else lines.append("- None")

    lines.extend(["", "## Errors", ""])
    lines.extend(f"- {item}" for item in result.errors) if result.errors else lines.append("- None")

    if result.out_of_scope:
        lines.extend(
            [
                "",
                "## Suggested Fix",
                "",
                "- Do not revert automatically.",
                "- Review the out-of-scope files with the user.",
                "- Either remove the out-of-scope changes manually or update the task allowed scope after explicit user confirmation.",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate modified files against a task's allowed scope.")
    parser.add_argument("--target", default=".", help="Target project directory. Defaults to current directory.")
    parser.add_argument("--task", required=True, help="Task file path, absolute or relative to target.")
    parser.add_argument("--base", default="HEAD", help="Git diff base. Defaults to HEAD.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    result = validate_scope(Path(args.target), Path(args.task), args.base)
    print(render_report(result), end="")
    return 1 if result.status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
