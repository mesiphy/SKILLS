#!/usr/bin/env python3
"""Archive a completed .ai active phase without deleting active content."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from summarize_handoff import summarize
from sync_status_md import sync_status_md


def load_status(target: Path) -> dict[str, Any]:
    path = target / ".ai" / "active" / "status.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"status.json not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"status.json is invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit("status.json must contain a JSON object")
    return value


def write_status(target: Path, status: dict[str, Any]) -> None:
    path = target / ".ai" / "active" / "status.json"
    path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def task_is_closed(task: dict[str, Any]) -> bool:
    status = task.get("status") or task.get("task_status")
    return status in {"review-pass", "waived"}


def ensure_closable(status: dict[str, Any]) -> None:
    if status.get("task_status") not in {"review-pass", "dev-done"}:
        raise SystemExit("Cannot archive: current task_status must be review-pass or dev-done with an explicit waiver.")
    tasks = status.get("tasks")
    if isinstance(tasks, list) and tasks:
        incomplete = []
        for task in tasks:
            if isinstance(task, dict) and not task_is_closed(task):
                incomplete.append(str(task.get("id") or task.get("task_id") or task.get("file") or "unknown"))
        if incomplete:
            raise SystemExit("Cannot archive: incomplete tasks: " + ", ".join(incomplete))


def slug(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or "completed-phase"


def archive_dir(target: Path, phase_name: str) -> Path:
    archive_root = target / ".ai" / "archive"
    archive_root.mkdir(parents=True, exist_ok=True)
    base = f"{datetime.now(timezone.utc).date().isoformat()}-{slug(phase_name)}"
    candidate = archive_root / base
    index = 2
    while candidate.exists():
        candidate = archive_root / f"{base}-{index:02d}"
        index += 1
    return candidate


def render_final_report(status: dict[str, Any]) -> str:
    goal = status.get("goal") if isinstance(status.get("goal"), dict) else {}
    tasks = status.get("tasks") if isinstance(status.get("tasks"), list) else []
    lines = [
        "# Final Report / 阶段总结",
        "",
        "## 1. Goal / 阶段目标",
        "",
        str(goal.get("name") or "TODO"),
        "",
        str(goal.get("description") or "TODO"),
        "",
        "## 2. Completed Tasks / 已完成任务",
        "",
        "| 编号 | 任务 | review | 证据 |",
        "|---|---|---|---|",
    ]
    if tasks:
        for task in tasks:
            if isinstance(task, dict):
                lines.append(
                    "| {id} | {name} | {review} | {dev_log} |".format(
                        id=task.get("id") or task.get("task_id") or "unknown",
                        name=task.get("name") or task.get("title") or "Untitled",
                        review=task.get("review_file") or task.get("review") or "See active review files",
                        dev_log=task.get("dev_log_file") or task.get("dev_log") or "See active dev-log files",
                    )
                )
    else:
        lines.append("| 无 | 无 | 无 | 无 |")
    lines.extend(
        [
            "",
            "## 3. Key Changes / 关键改动",
            "",
            "- See task dev-logs and reviews.",
            "",
            "## 4. Verification / 验证结果",
            "",
            "- See task dev-logs and reviews.",
            "",
            "## 5. Unverified / 未验证项",
            "",
            "- TODO",
            "",
            "## 6. Risks / 遗留风险",
            "",
            "- TODO",
            "",
            "## 7. Next Handoff / 下一阶段交接",
            "",
            "- See `.ai/handoff/latest-summary.md`.",
            "",
        ]
    )
    return "\n".join(lines)


def archive_phase(target: Path, phase_name: str | None) -> Path:
    target = target.resolve()
    active = target / ".ai" / "active"
    if not active.is_dir():
        raise SystemExit("Cannot archive: .ai/active directory is missing.")

    status = load_status(target)
    ensure_closable(status)
    status["phase"] = "completed"
    status["task_status"] = "review-pass"
    status["updated_at"] = datetime.now(timezone.utc).isoformat()
    status["updated_by"] = "archive_phase.py"
    write_status(target, status)
    sync_status_md(target)

    final_report = active / "final-report.md"
    if not final_report.exists():
        final_report.write_text(render_final_report(status), encoding="utf-8")

    summarize(target)

    goal = status.get("goal") if isinstance(status.get("goal"), dict) else {}
    archive_name = phase_name or str(goal.get("name") or "completed-phase")
    dest = archive_dir(target, archive_name)
    shutil.copytree(active, dest)
    shutil.copy2(active / "status.md", dest / "status.final.md")
    return dest


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Archive a completed active phase.")
    parser.add_argument("--target", default=".", help="Target project directory. Defaults to current directory.")
    parser.add_argument("--phase-name", help="Optional archive slug source. Defaults to goal name or completed-phase.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    dest = archive_phase(Path(args.target), args.phase_name)
    print(f"Archived active phase to {dest.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
