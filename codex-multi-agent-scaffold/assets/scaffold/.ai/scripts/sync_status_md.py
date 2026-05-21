#!/usr/bin/env python3
"""Render .ai/active/status.md from .ai/active/status.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_status(target: Path) -> dict[str, Any]:
    status_path = target / ".ai" / "active" / "status.json"
    try:
        status = json.loads(status_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"status.json not found: {status_path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"status.json is invalid JSON: {exc}") from exc

    if not isinstance(status, dict):
        raise SystemExit("status.json must contain a JSON object")
    return status


def text_or_uncreated(value: Any) -> str:
    if value in {None, ""}:
        return "未创建"
    return str(value)


def code_or_uncreated(value: Any) -> str:
    if value in {None, ""}:
        return "未创建"
    return str(value)


def confirmation_rows(confirmations: Any, last_confirmation: Any) -> list[str]:
    if isinstance(confirmations, list) and confirmations:
        rows: list[str] = []
        for item in confirmations:
            if isinstance(item, dict):
                rows.append(
                    "| {time} | {task} | {question} | {decision} | {action} |".format(
                        time=item.get("time") or "未知",
                        task=item.get("task") or "未知",
                        question=item.get("question") or "未知",
                        decision=item.get("decision") or "未知",
                        action=item.get("action") or "未知",
                    )
                )
            else:
                rows.append(f"| 未知 | 未知 | 用户确认 | {item} | 未知 |")
        return rows

    if last_confirmation:
        return [f"| 未知 | 当前任务 | 用户确认 | {last_confirmation} | 允许流程推进 |"]

    return ["| 无 | 无 | 无 | 无 | 无 |"]


def task_rows(tasks: Any) -> list[str]:
    if not isinstance(tasks, list) or not tasks:
        return ["| 无 | 无 | 无 | 无 | `pending` | 未创建 | 未创建 | 等待 plan mode 生成任务 |"]

    rows: list[str] = []
    for index, task in enumerate(tasks, start=1):
        if not isinstance(task, dict):
            rows.append(f"| {index:03d} | 未知 | 非法任务项 | 无 | `blocked` | 未创建 | 未创建 | tasks[{index - 1}] 不是对象 |")
            continue
        task_id = task.get("id") or task.get("task_id") or f"{index:03d}"
        rows.append(
            "| {id} | {file} | {name} | {depends} | `{status}` | {dev_log} | {review} | {notes} |".format(
                id=task_id,
                file=task.get("file") or task.get("task_file") or "未创建",
                name=task.get("name") or task.get("title") or "未命名",
                depends=", ".join(task.get("depends_on") or []) if isinstance(task.get("depends_on"), list) else task.get("depends_on") or "无",
                status=task.get("status") or task.get("task_status") or "pending",
                dev_log=task.get("dev_log") or task.get("dev_log_file") or "未创建",
                review=task.get("review") or task.get("review_file") or "未创建",
                notes=task.get("notes") or "无",
            )
        )
    return rows


def blocker_rows(blockers: Any, blocked_reason: Any) -> list[str]:
    if isinstance(blockers, list) and blockers:
        rows: list[str] = []
        for item in blockers:
            if isinstance(item, dict):
                rows.append(
                    "| {kind} | {description} | {scope} | {handling} |".format(
                        kind=item.get("type") or "阻塞",
                        description=item.get("description") or "未说明",
                        scope=item.get("scope") or "未知",
                        handling=item.get("handling") or "待处理",
                    )
                )
            else:
                rows.append(f"| 阻塞 | {item} | 未知 | 待处理 |")
        return rows

    if blocked_reason:
        return [f"| 阻塞 | {blocked_reason} | 当前流程 | 待处理 |"]

    return ["| 无 | 无 | 无 | 无 |"]


def render_status_md(status: dict[str, Any]) -> str:
    phase = status.get("phase") or "planning"
    task_status = status.get("task_status") or "pending"
    current_task_id = status.get("current_task_id")
    current_task_name = status.get("current_task_name")
    current_task_file = status.get("current_task_file")
    dev_log_file = status.get("dev_log_file")
    review_file = status.get("review_file")
    blocked_reason = status.get("blocked_reason")
    updated_at = status.get("updated_at") or "YYYY-MM-DD HH:mm Timezone"
    updated_by = status.get("updated_by") or status.get("last_updated_by") or "workflow-script"
    goal = status.get("goal") if isinstance(status.get("goal"), dict) else {}

    lines = [
        "# AI Development Status / AI 开发状态",
        "",
        "本文档是当前阶段的人类可读运行状态。机器可读状态以 `.ai/active/status.json` 为准。",
        "",
        "所有 agent 必须先读取 `.ai/rules.md`，再读取 `.ai/active/status.json`，最后读取本文档。如果本文档与 `status.json` 冲突，必须暂停并运行状态校验。",
        "",
        "## 1. Current Goal / 当前目标",
        "",
        "### Goal Name / 目标名称",
        "",
        f"`{goal.get('name') or 'TODO'}`",
        "",
        "### Goal Description / 目标描述",
        "",
        str(goal.get("description") or "TODO"),
        "",
        "### Action Plan / 对应计划",
        "",
        "```text",
        ".ai/active/action-plan.md",
        "```",
        "",
        "## 2. Flow State / 流程状态",
        "",
        "### Current Phase / 当前阶段",
        "",
        f"`{phase}`",
        "",
        "### Current Task Status / 当前任务状态",
        "",
        f"`{task_status}`",
        "",
        "### Last Updated / 最近一次更新",
        "",
        "```text",
        str(updated_at),
        "```",
        "",
        "### Last Updated By / 最近更新者",
        "",
        f"`{updated_by}`",
        "",
        "## 3. Current Task / 当前任务",
        "",
        "### Task ID / 当前任务编号",
        "",
        f"`{text_or_uncreated(current_task_id)}`",
        "",
        "### Task Name / 当前任务名称",
        "",
        f"`{text_or_uncreated(current_task_name)}`",
        "",
        "### Task File / 当前任务文件",
        "",
        "```text",
        code_or_uncreated(current_task_file),
        "```",
        "",
        "### Current Dev Log / 当前 dev-log",
        "",
        "```text",
        code_or_uncreated(dev_log_file),
        "```",
        "",
        "### Current Review / 当前 review",
        "",
        "```text",
        code_or_uncreated(review_file),
        "```",
        "",
        "### Blocker / 当前任务阻塞原因",
        "",
        f"`{blocked_reason or '无'}`",
        "",
        "## 4. Task Overview / 任务总览",
        "",
        "| 编号 | 任务文件 | 任务名称 | 依赖 | 状态 | dev-log | review | 备注 |",
        "|---|---|---|---|---|---|---|---|",
        *task_rows(status.get("tasks")),
        "",
        "## 5. Fix Records / 返工记录",
        "",
        "| 原任务 | 失败 review | 返工任务 | 返工状态 | 说明 |",
        "|---|---|---|---|---|",
        "| 无 | 无 | 无 | 无 | 当前没有返工任务 |",
        "",
        "## 6. Human Confirmations / 人工确认记录",
        "",
        "| 时间 | 触发任务 | 问题 | 用户结论 | 后续动作 |",
        "|---|---|---|---|---|",
        *confirmation_rows(status.get("human_confirmations"), status.get("last_human_confirmation")),
        "",
        "## 7. Global Blockers and Risks / 全局阻塞与风险",
        "",
        "| 类型 | 描述 | 影响范围 | 当前处理方式 |",
        "|---|---|---|---|",
        *blocker_rows(status.get("blockers"), blocked_reason),
        "",
    ]

    return "\n".join(lines)


def sync_status_md(target: Path, check: bool = False) -> bool:
    target = target.resolve()
    status = load_status(target)
    rendered = render_status_md(status)
    status_md_path = target / ".ai" / "active" / "status.md"
    current = status_md_path.read_text(encoding="utf-8") if status_md_path.exists() else None
    if check:
        return current == rendered
    status_md_path.parent.mkdir(parents=True, exist_ok=True)
    status_md_path.write_text(rendered, encoding="utf-8")
    return True


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render .ai/active/status.md from status.json.")
    parser.add_argument("--target", default=".", help="Target project directory. Defaults to current directory.")
    parser.add_argument("--check", action="store_true", help="Exit nonzero if status.md is not synchronized.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    target = Path(args.target)
    ok = sync_status_md(target, check=args.check)
    if args.check:
        print("status.md is synchronized." if ok else "status.md is not synchronized.")
        return 0 if ok else 1
    print(f"Updated {(target / '.ai' / 'active' / 'status.md').as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
