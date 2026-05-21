#!/usr/bin/env python3
"""Generate .ai/handoff/latest-summary.md from current active state."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
    return value if isinstance(value, dict) else {}


def read_excerpt(path: Path, limit: int = 4000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit].strip()
    except OSError:
        return ""


def task_lines(tasks: Any) -> list[str]:
    if not isinstance(tasks, list) or not tasks:
        return ["- No tasks recorded."]
    lines: list[str] = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        lines.append(
            "- `{id}` `{status}` {name} ({file})".format(
                id=task.get("id") or task.get("task_id") or "unknown",
                status=task.get("status") or task.get("task_status") or "unknown",
                name=task.get("name") or task.get("title") or "Untitled",
                file=task.get("file") or task.get("task_file") or "no file",
            )
        )
    return lines or ["- No valid task entries recorded."]


def render_summary(target: Path) -> str:
    active = target / ".ai" / "active"
    status = load_json(active / "status.json")
    final_report = read_excerpt(active / "final-report.md")
    action_plan = read_excerpt(active / "action-plan.md", limit=2000)
    goal = status.get("goal") if isinstance(status.get("goal"), dict) else {}

    lines = [
        "# Latest Handoff Summary / 最新交接摘要",
        "",
        f"- Generated at: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Phase: `{status.get('phase') or 'unknown'}`",
        f"- Task status: `{status.get('task_status') or 'unknown'}`",
        f"- Goal: `{goal.get('name') or 'TODO'}`",
        "",
        "## Completed or Current Tasks",
        "",
        *task_lines(status.get("tasks")),
        "",
        "## Final Report Excerpt",
        "",
        final_report or "No final report exists yet.",
        "",
        "## Action Plan Excerpt",
        "",
        action_plan or "No action plan content recorded.",
        "",
        "## Next Phase Notes",
        "",
        "- Read this summary, then `.ai/project-context.md`, `.ai/project-specific-rules.md`, and current active status.",
        "- Do not read `.ai/archive/**` unless historical investigation is explicitly requested.",
        "",
    ]
    return "\n".join(lines)


def summarize(target: Path) -> Path:
    target = target.resolve()
    handoff = target / ".ai" / "handoff" / "latest-summary.md"
    handoff.parent.mkdir(parents=True, exist_ok=True)
    handoff.write_text(render_summary(target), encoding="utf-8")
    return handoff


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate latest handoff summary.")
    parser.add_argument("--target", default=".", help="Target project directory. Defaults to current directory.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    path = summarize(Path(args.target))
    print(f"Updated {path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
