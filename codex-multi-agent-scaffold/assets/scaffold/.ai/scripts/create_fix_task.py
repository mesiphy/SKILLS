#!/usr/bin/env python3
"""Create a focused fix task from review-failed or need-human-review state."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sync_status_md import sync_status_md


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


def project_path(target: Path, value: Any) -> Path:
    if not value:
        raise SystemExit("Required status path is empty.")
    path = Path(str(value))
    return path if path.is_absolute() else target / path


def require_file(target: Path, label: str, value: Any) -> str:
    path = project_path(target, value)
    if not path.is_file():
        raise SystemExit(f"Cannot create fix task: {label} does not exist: {value}")
    try:
        return path.relative_to(target).as_posix()
    except ValueError:
        return path.as_posix()


def next_fix_id(task_dir: Path, base_id: str) -> str:
    highest = 0
    pattern = re.compile(rf"^{re.escape(base_id)}-fix-(\d+)-task\.md$")
    for path in task_dir.glob(f"{base_id}-fix-*-task.md"):
        match = pattern.match(path.name)
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{base_id}-fix-{highest + 1:02d}"


def render_fix_task(fix_id: str, original_task: str, original_dev_log: str, original_review: str, reason: str) -> str:
    return f"""# {fix_id} - Fix Task / 返工任务

## Fix Task File / 返工任务文件

- `.ai/active/current-task/{fix_id}-task.md`

## Fix Goal / 返工目标

Resolve the issues documented in `{original_review}`.

## Original Task / 原任务

- `{original_task}`

## Original Dev Log / 原 dev-log

- `{original_dev_log}`

## Trigger Review / 触发返工的 review

- `{original_review}`

## Issues to Fix / 需要修复的问题

- {reason}

## Allowed Scope / 允许修改范围

- Same product-code scope as the original task unless the user explicitly approves expansion.
- `.ai/active/dev-log/{fix_id}-dev-log.md`
- `.ai/active/status.json`
- `.ai/active/status.md`

## Forbidden Scope / 禁止修改范围

- Do not expand beyond review findings without explicit user approval.
- Do not overwrite the original task, dev-log, or review.

## Steps / 返工步骤

1. Re-read the original task, dev-log, and triggering review.
2. Fix only the reviewed issues.
3. Run required verification.
4. Create `.ai/active/dev-log/{fix_id}-dev-log.md`.
5. Update status to `reviewing/dev-done`.

## Acceptance Criteria / 返工验收标准

- Every issue from `{original_review}` is addressed or explicitly escalated.
- Scope remains within the original task unless user-approved.
- Required verification is run or the reason it cannot run is recorded.

## Required Outputs / 输出要求

- `.ai/active/dev-log/{fix_id}-dev-log.md`
- Updated `.ai/active/status.json`
- Updated `.ai/active/status.md`
- Wait for review.
"""


def create_fix_task(target: Path, reason: str) -> str:
    target = target.resolve()
    status = load_status(target)
    if status.get("task_status") not in {"review-failed", "need-human-review"}:
        raise SystemExit("Cannot create fix task: task_status must be review-failed or need-human-review.")

    base_id = str(status.get("current_task_id") or "task")
    original_task = require_file(target, "current_task_file", status.get("current_task_file"))
    original_dev_log = require_file(target, "dev_log_file", status.get("dev_log_file"))
    original_review = require_file(target, "review_file", status.get("review_file"))

    task_dir = target / ".ai" / "active" / "current-task"
    task_dir.mkdir(parents=True, exist_ok=True)
    fix_id = next_fix_id(task_dir, base_id)
    fix_file = f".ai/active/current-task/{fix_id}-task.md"
    fix_path = target / fix_file
    if fix_path.exists():
        raise SystemExit(f"Cannot create fix task: file already exists: {fix_file}")
    fix_path.write_text(render_fix_task(fix_id, original_task, original_dev_log, original_review, reason), encoding="utf-8")

    tasks = status.setdefault("tasks", [])
    if not isinstance(tasks, list):
        raise SystemExit("Cannot create fix task: status.tasks must be an array.")
    tasks.append(
        {
            "id": fix_id,
            "name": f"Fix {base_id}",
            "file": fix_file,
            "status": "pending",
            "depends_on": [base_id],
            "notes": f"Created from {original_review}",
        }
    )

    status["phase"] = "fixing"
    status["current_task_id"] = fix_id
    status["current_task_name"] = f"Fix {base_id}"
    status["current_task_file"] = fix_file
    status["task_status"] = "pending"
    status["dev_log_file"] = None
    status["review_file"] = None
    status["blocked_reason"] = None
    status["updated_at"] = datetime.now(timezone.utc).isoformat()
    status["updated_by"] = "create_fix_task.py"
    write_status(target, status)
    sync_status_md(target)
    return fix_file


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a fix task from a failed or human-review state.")
    parser.add_argument("--target", default=".", help="Target project directory. Defaults to current directory.")
    parser.add_argument("--reason", default="Address the failed review findings.", help="Short fix reason to include in the task.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    fix_file = create_fix_task(Path(args.target), args.reason)
    print(f"Created fix task: {fix_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
