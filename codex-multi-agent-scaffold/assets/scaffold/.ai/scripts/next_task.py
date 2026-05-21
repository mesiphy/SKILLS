#!/usr/bin/env python3
"""Advance from a review-pass task to the next pending task."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sync_status_md import sync_status_md


DEFAULT_CONFIG = {
    "review.auto_advance_on_review_pass": False,
    "execution.max_tasks_per_run": 1,
}


def load_status(target: Path) -> dict[str, Any]:
    path = target / ".ai" / "active" / "status.json"
    try:
        status = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"status.json not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"status.json is invalid JSON: {exc}") from exc
    if not isinstance(status, dict):
        raise SystemExit("status.json must contain a JSON object")
    return status


def write_status(target: Path, status: dict[str, Any]) -> None:
    path = target / ".ai" / "active" / "status.json"
    path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    try:
        return int(value)
    except ValueError:
        return value.strip("\"'")


def load_config(target: Path) -> dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    path = target / ".ai" / "workflow-config.yaml"
    if not path.exists():
        return config

    section: str | None = None
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if not line.startswith(" ") and line.endswith(":"):
            section = line[:-1].strip()
            continue
        if section and ":" in line:
            key, value = line.strip().split(":", 1)
            config[f"{section}.{key.strip()}"] = parse_scalar(value)
    return config


def project_file(target: Path, value: Any) -> Path | None:
    if not value:
        return None
    path = Path(str(value))
    return path if path.is_absolute() else target / path


def require_file(target: Path, label: str, value: Any) -> None:
    path = project_file(target, value)
    if not path or not path.is_file():
        raise SystemExit(f"Cannot advance: {label} is missing or does not exist: {value}")


def task_status(task: dict[str, Any]) -> str:
    return str(task.get("status") or task.get("task_status") or "pending")


def set_task_status(task: dict[str, Any], value: str) -> None:
    if "task_status" in task and "status" not in task:
        task["task_status"] = value
    else:
        task["status"] = value


def task_id(task: dict[str, Any]) -> Any:
    return task.get("id") or task.get("task_id")


def task_file(task: dict[str, Any]) -> Any:
    return task.get("file") or task.get("task_file")


def matches_current(task: dict[str, Any], status: dict[str, Any]) -> bool:
    current_id = status.get("current_task_id")
    current_file = status.get("current_task_file")
    return bool((current_id and task_id(task) == current_id) or (current_file and task_file(task) == current_file))


def advance(target: Path, confirm: str | None) -> str:
    target = target.resolve()
    status = load_status(target)
    config = load_config(target)

    if status.get("task_status") != "review-pass":
        raise SystemExit("Cannot advance: current task_status must be review-pass.")

    require_file(target, "dev_log_file", status.get("dev_log_file"))
    require_file(target, "review_file", status.get("review_file"))

    auto_advance = bool(config.get("review.auto_advance_on_review_pass", False))
    if confirm:
        status["last_human_confirmation"] = f"{datetime.now(timezone.utc).isoformat()} {confirm}"
    elif not auto_advance and not status.get("last_human_confirmation"):
        raise SystemExit("Cannot advance: explicit human confirmation is required.")

    max_tasks = config.get("execution.max_tasks_per_run", 1)
    if not isinstance(max_tasks, int) or max_tasks < 1:
        raise SystemExit("Cannot advance: execution.max_tasks_per_run must be at least 1.")

    tasks = status.get("tasks")
    if not isinstance(tasks, list):
        raise SystemExit("Cannot advance: status.json tasks must be an array.")

    for task in tasks:
        if isinstance(task, dict) and matches_current(task, status):
            set_task_status(task, "review-pass")
            task["dev_log_file"] = status.get("dev_log_file")
            task["review_file"] = status.get("review_file")

    next_task: dict[str, Any] | None = None
    for task in tasks:
        if isinstance(task, dict) and task_status(task) == "pending":
            next_task = task
            break

    now = datetime.now(timezone.utc).isoformat()
    status["updated_at"] = now
    status["updated_by"] = "next_task.py"
    status["blocked_reason"] = None

    if next_task is None:
        status["phase"] = "completed"
        status["task_status"] = "review-pass"
        write_status(target, status)
        sync_status_md(target)
        return "No pending task remains. Marked phase completed; run phase-close to generate final-report and archive."

    status["phase"] = "ready"
    status["current_task_id"] = task_id(next_task)
    status["current_task_name"] = next_task.get("name") or next_task.get("title")
    status["current_task_file"] = task_file(next_task)
    status["task_status"] = "pending"
    status["dev_log_file"] = None
    status["review_file"] = None
    set_task_status(next_task, "pending")

    if not status["current_task_file"]:
        raise SystemExit("Cannot advance: next pending task has no file/task_file value.")
    require_file(target, "next current_task_file", status["current_task_file"])

    write_status(target, status)
    sync_status_md(target)
    return f"Advanced to next task: {status['current_task_id']} ({status['current_task_file']})."


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Advance to the next pending task after review-pass.")
    parser.add_argument("--target", default=".", help="Target project directory. Defaults to current directory.")
    parser.add_argument("--confirm", help="Explicit human confirmation text to record before advancing.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    message = advance(Path(args.target), confirm=args.confirm)
    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
