# AI Development Status / AI 开发状态

使用 `.ai/active/status.json` 作为机器可读状态，使用 `.ai/active/status.md` 作为人类可读状态。两个文件必须同步更新。

## status.json Required Shape

```json
{
  "phase": "planning",
  "current_task_id": null,
  "current_task_file": null,
  "task_status": "pending",
  "dev_log_file": null,
  "review_file": null,
  "last_human_confirmation": null,
  "tasks": [],
  "blocked_reason": null,
  "updated_at": null
}
```

## Legal Phase Values

- `planning`
- `ready`
- `developing`
- `reviewing`
- `fixing`
- `paused`
- `blocked`
- `completed`

## Legal Task Status Values

- `pending`
- `in-progress`
- `dev-done`
- `review-pass`
- `review-failed`
- `need-human-review`
- `blocked`

## Sync Rules

- Update `status.json` first, then mirror the same state into `status.md`.
- `status.md` may contain richer tables and notes, but it must not contradict `status.json`.
- If the files conflict, stop and run validation before continuing.
- Do not infer human confirmation; record it only when the user explicitly confirms.
