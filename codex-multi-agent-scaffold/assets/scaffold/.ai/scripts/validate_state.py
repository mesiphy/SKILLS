#!/usr/bin/env python3
"""Validate a project's .ai workflow scaffold and active state."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


LEGAL_PHASES = {
    "planning",
    "ready",
    "developing",
    "reviewing",
    "fixing",
    "paused",
    "blocked",
    "completed",
}

LEGAL_TASK_STATUSES = {
    "pending",
    "in-progress",
    "dev-done",
    "review-pass",
    "review-failed",
    "need-human-review",
    "blocked",
}

REQUIRED_STATUS_KEYS = {
    "phase",
    "current_task_id",
    "current_task_file",
    "task_status",
    "dev_log_file",
    "review_file",
    "last_human_confirmation",
    "tasks",
    "blocked_reason",
    "updated_at",
}

OPTIONAL_STATUS_KEYS = {
    "blockers",
    "current_task_name",
    "goal",
    "human_confirmations",
    "last_updated_by",
    "updated_by",
}


@dataclass
class Check:
    level: str
    name: str
    detail: str
    fix: str | None = None


def add(checks: list[Check], level: str, name: str, detail: str, fix: str | None = None) -> None:
    checks.append(Check(level=level, name=name, detail=detail, fix=fix))


def load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, f"File not found: {path}"
    except json.JSONDecodeError as exc:
        return None, f"Invalid JSON: {exc}"
    except OSError as exc:
        return None, f"Cannot read file: {exc}"

    if not isinstance(value, dict):
        return None, "status.json must contain a JSON object"
    return value, None


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def project_path(target: Path, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return target / path


def has_task_files(task_dir: Path) -> list[Path]:
    if not task_dir.is_dir():
        return []
    return sorted(path for path in task_dir.glob("*.md") if path.is_file())


def parse_status_md(path: Path) -> dict[str, str | None]:
    text = read_text(path)
    if not text:
        return {}

    fields = {
        "phase": extract_after_heading(text, "Current Phase"),
        "task_status": extract_after_heading(text, "Current Task Status"),
        "current_task_id": extract_after_heading(text, "Task ID"),
        "current_task_file": extract_code_block_after_heading(text, "Task File"),
        "dev_log_file": extract_code_block_after_heading(text, "Current Dev Log"),
        "review_file": extract_code_block_after_heading(text, "Current Review"),
    }

    return {key: normalize_empty(value) for key, value in fields.items()}


def normalize_empty(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if value in {"", "null", "None", "未创建", "无", "N/A", "Unknown"}:
        return None
    return value


def extract_after_heading(text: str, heading: str) -> str | None:
    pattern = re.compile(
        rf"^### .*\b{re.escape(heading)}\b.*?\n\n`([^`]+)`",
        re.MULTILINE,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else None


def extract_code_block_after_heading(text: str, heading: str) -> str | None:
    pattern = re.compile(
        rf"^### .*\b{re.escape(heading)}\b.*?\n\n```text\n(.*?)\n```",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if match:
        return match.group(1).strip()
    return extract_after_heading(text, heading)


def validate(target: Path, strict: bool) -> list[Check]:
    checks: list[Check] = []
    target = target.resolve()
    ai = target / ".ai"
    active = ai / "active"
    current_task_dir = active / "current-task"
    dev_log_dir = active / "dev-log"
    review_dir = active / "review"
    archive_dir = ai / "archive"
    handoff_dir = ai / "handoff"

    required_files = [
        target / "AGENTS.md",
        ai / "rules.md",
        ai / "repo-scan-report.md",
        ai / "project-context.md",
        ai / "project-specific-rules.md",
        ai / "workflow-config.yaml",
        active / "status.md",
        active / "status.json",
        active / "action-plan.md",
        ai / "scripts" / "archive_phase.py",
        ai / "scripts" / "create_fix_task.py",
        ai / "scripts" / "next_task.py",
        ai / "scripts" / "summarize_handoff.py",
        ai / "scripts" / "sync_status_md.py",
        ai / "scripts" / "validate_state.py",
        target / ".codex" / "agents" / "developer.toml",
        target / ".codex" / "agents" / "explorer.toml",
        target / ".codex" / "agents" / "fix-planner.toml",
        target / ".codex" / "agents" / "flow-controller.toml",
        target / ".codex" / "agents" / "orchestrator.toml",
        target / ".codex" / "agents" / "planner.toml",
        target / ".codex" / "agents" / "reviewer.toml",
    ]
    required_dirs = [
        target / ".codex",
        target / ".codex" / "agents",
        ai,
        active,
        current_task_dir,
        dev_log_dir,
        review_dir,
        archive_dir,
        handoff_dir,
        ai / "scripts",
    ]

    for directory in required_dirs:
        if directory.is_dir():
            add(checks, "PASS", f"Directory exists: {directory.relative_to(target)}", "Found.")
        else:
            add(
                checks,
                "FAIL",
                f"Directory missing: {directory.relative_to(target)}",
                "Required workflow directory is missing.",
                f"Create `{directory.relative_to(target)}/` or rerun init_scaffold.py.",
            )

    for file_path in required_files:
        if file_path.is_file():
            add(checks, "PASS", f"File exists: {file_path.relative_to(target)}", "Found.")
        else:
            add(
                checks,
                "FAIL",
                f"File missing: {file_path.relative_to(target)}",
                "Required workflow file is missing.",
                f"Restore `{file_path.relative_to(target)}` from the scaffold or rerun init_scaffold.py.",
            )

    status_json_path = active / "status.json"
    status, status_error = load_json(status_json_path)
    if status_error:
        add(checks, "FAIL", "status.json parse", status_error, "Fix JSON syntax or restore the status.json template.")
        status = {}
    else:
        add(checks, "PASS", "status.json parse", "Valid JSON object.")

    missing_keys = sorted(REQUIRED_STATUS_KEYS - set(status.keys()))
    extra_keys = sorted(set(status.keys()) - REQUIRED_STATUS_KEYS - OPTIONAL_STATUS_KEYS)
    if missing_keys:
        add(
            checks,
            "FAIL",
            "status.json required keys",
            "Missing keys: " + ", ".join(missing_keys),
            "Add the missing keys using the status.json template.",
        )
    else:
        add(checks, "PASS", "status.json required keys", "All required keys are present.")

    if extra_keys:
        add(checks, "WARN", "status.json extra keys", "Extra keys: " + ", ".join(extra_keys))

    phase = status.get("phase")
    task_status = status.get("task_status")

    if phase in LEGAL_PHASES:
        add(checks, "PASS", "phase enum", f"`{phase}` is legal.")
    else:
        add(
            checks,
            "FAIL",
            "phase enum",
            f"`{phase}` is not legal.",
            "Use one of: " + ", ".join(sorted(LEGAL_PHASES)),
        )

    if task_status in LEGAL_TASK_STATUSES:
        add(checks, "PASS", "task_status enum", f"`{task_status}` is legal.")
    else:
        add(
            checks,
            "FAIL",
            "task_status enum",
            f"`{task_status}` is not legal.",
            "Use one of: " + ", ".join(sorted(LEGAL_TASK_STATUSES)),
        )

    if not isinstance(status.get("tasks"), list):
        add(checks, "FAIL", "status.json tasks type", "`tasks` must be an array.")
    else:
        add(checks, "PASS", "status.json tasks type", "`tasks` is an array.")
        validate_task_items(checks, status["tasks"])

    task_files = has_task_files(current_task_dir)
    if task_files:
        add(checks, "PASS", "current-task files", f"Found {len(task_files)} task file(s).")
    else:
        if phase == "planning" and not status.get("current_task_file") and status.get("tasks") == []:
            add(
                checks,
                "PASS",
                "current-task files",
                "No task files found; valid before plan mode creates tasks.",
            )
        else:
            add(
                checks,
                "FAIL",
                "current-task files",
                "No task files found in `.ai/active/current-task/`.",
                "Generate current-task files in plan mode when a development goal is active.",
            )

    check_referenced_file(
        checks,
        target,
        "current_task_file",
        status.get("current_task_file"),
        required_when=phase in {"ready", "developing", "reviewing", "fixing", "paused"},
    )
    check_referenced_file(
        checks,
        target,
        "dev_log_file",
        status.get("dev_log_file"),
        required_when=task_status in {"dev-done", "review-pass", "review-failed", "need-human-review"},
    )
    check_referenced_file(
        checks,
        target,
        "review_file",
        status.get("review_file"),
        required_when=task_status in {"review-pass", "review-failed", "need-human-review"},
    )

    if task_status == "review-pass" and not status.get("review_file"):
        add(checks, "FAIL", "review-pass review file", "review-pass requires `review_file`.", "Set `review_file` to the passing review file.")

    if task_status == "review-failed":
        current_task_id = status.get("current_task_id")
        pattern = f"{current_task_id}-fix-*-task.md" if current_task_id else "*fix-*-task.md"
        fix_tasks = list(current_task_dir.glob(pattern))
        if fix_tasks:
            add(checks, "PASS", "review-failed fix task", f"Found {len(fix_tasks)} fix task(s).")
        else:
            add(
                checks,
                "FAIL",
                "review-failed fix task",
                "review-failed requires a fix task.",
                "Run fix-planning mode to create a focused fix task.",
            )

    if phase == "completed":
        final_report = active / "final-report.md"
        if final_report.is_file():
            add(checks, "PASS", "completed final report", "final-report.md exists.")
        else:
            add(
                checks,
                "FAIL",
                "completed final report",
                "completed phase requires `.ai/active/final-report.md`.",
                "Run phase-close mode to generate the final report before marking completed.",
            )

    status_md_path = active / "status.md"
    if status_md_path.is_file():
        compare_status_md(checks, status, parse_status_md(status_md_path))

    detect_state_conflicts(checks, status)

    if strict:
        for index, check in enumerate(checks):
            if check.level == "WARN":
                checks[index] = Check(
                    level="FAIL",
                    name=check.name,
                    detail="Strict mode: " + check.detail,
                    fix=check.fix,
                )

    return checks


def validate_task_items(checks: list[Check], tasks: list[Any]) -> None:
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            add(checks, "FAIL", f"tasks[{index}]", "Task entry must be an object.")
            continue
        status = task.get("status") or task.get("task_status")
        if status and status not in LEGAL_TASK_STATUSES:
            add(
                checks,
                "FAIL",
                f"tasks[{index}] status",
                f"`{status}` is not legal.",
                "Use one of: " + ", ".join(sorted(LEGAL_TASK_STATUSES)),
            )


def check_referenced_file(
    checks: list[Check],
    target: Path,
    key: str,
    value: Any,
    required_when: bool,
) -> None:
    if value in {None, ""}:
        if required_when:
            add(checks, "FAIL", key, f"`{key}` is required in the current state.", f"Set `{key}` to an existing .ai file.")
        else:
            add(checks, "PASS", key, f"`{key}` is not set and is not required in this state.")
        return

    if not isinstance(value, str):
        add(checks, "FAIL", key, f"`{key}` must be a string path or null.")
        return

    path = project_path(target, value)
    if path and path.is_file():
        add(checks, "PASS", key, f"`{value}` exists.")
    else:
        add(checks, "FAIL", key, f"`{value}` does not exist.", f"Create `{value}` or update `{key}`.")


def compare_status_md(checks: list[Check], status_json: dict[str, Any], status_md: dict[str, str | None]) -> None:
    comparable = {
        "phase": status_json.get("phase"),
        "task_status": status_json.get("task_status"),
        "current_task_id": status_json.get("current_task_id"),
        "current_task_file": status_json.get("current_task_file"),
        "dev_log_file": status_json.get("dev_log_file"),
        "review_file": status_json.get("review_file"),
    }

    conflicts: list[str] = []
    for key, json_value in comparable.items():
        md_value = status_md.get(key)
        if md_value is None:
            continue
        if json_value != md_value:
            conflicts.append(f"{key}: status.json=`{json_value}` status.md=`{md_value}`")

    if conflicts:
        add(
            checks,
            "FAIL",
            "status.md/status.json sync",
            "; ".join(conflicts),
            "Update status.md and status.json so they describe the same active state.",
        )
    else:
        add(checks, "PASS", "status.md/status.json sync", "No parsed conflicts found.")


def detect_state_conflicts(checks: list[Check], status: dict[str, Any]) -> None:
    phase = status.get("phase")
    task_status = status.get("task_status")
    blocked_reason = status.get("blocked_reason")

    conflicts: list[str] = []
    if phase == "blocked" and not blocked_reason:
        conflicts.append("blocked phase requires blocked_reason")
    if phase == "developing" and task_status != "in-progress":
        conflicts.append("developing phase should use task_status in-progress")
    if phase == "reviewing" and task_status != "dev-done":
        conflicts.append("reviewing phase should use task_status dev-done")
    if phase == "paused" and task_status not in {"review-pass", "need-human-review", "blocked"}:
        conflicts.append("paused phase should use review-pass, need-human-review, or blocked")
    if phase == "completed" and task_status not in {"review-pass", "dev-done"}:
        conflicts.append("completed phase should follow completed work")

    if conflicts:
        add(
            checks,
            "FAIL",
            "state conflicts",
            "; ".join(conflicts),
            "Update phase/task_status/blocked_reason to a legal state machine combination.",
        )
    else:
        add(checks, "PASS", "state conflicts", "No state conflicts detected.")


def render_report(target: Path, checks: list[Check]) -> str:
    counts = {
        "PASS": sum(1 for check in checks if check.level == "PASS"),
        "WARN": sum(1 for check in checks if check.level == "WARN"),
        "FAIL": sum(1 for check in checks if check.level == "FAIL"),
    }
    overall = "FAIL" if counts["FAIL"] else "WARN" if counts["WARN"] else "PASS"

    lines = [
        "# AI State Validation Report",
        "",
        f"- Target: `{target.resolve().as_posix()}`",
        f"- Overall: `{overall}`",
        f"- PASS: `{counts['PASS']}`",
        f"- WARN: `{counts['WARN']}`",
        f"- FAIL: `{counts['FAIL']}`",
        "",
        "## Checks",
        "",
    ]

    for check in checks:
        lines.append(f"### {check.level}: {check.name}")
        lines.append("")
        lines.append(check.detail)
        if check.fix:
            lines.append("")
            lines.append(f"Suggested fix: {check.fix}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a project's .ai workflow state.")
    parser.add_argument("--target", default=".", help="Target project directory. Defaults to current directory.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    target = Path(args.target)
    checks = validate(target=target, strict=args.strict)
    print(render_report(target, checks), end="")
    return 1 if any(check.level == "FAIL" for check in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
