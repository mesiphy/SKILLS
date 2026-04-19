---
name: git-obsidian-sync
description: Review and sync Obsidian or Markdown notes in a git repository. Use when the user asks to sync notes, commit recent Obsidian edits, push just-written Markdown files, or generate per-file commit summaries before syncing. This skill inspects current git changes, filters to Markdown note files, produces a per-file preview, waits for confirmation, then syncs one file per commit and push.
---

# Git Obsidian Sync

## Overview

Use this skill to turn changed Obsidian notes into a confirmation-first git sync workflow. Prefer existing git commands and built-in agent capabilities; do not create helper scripts or invent a separate sync mechanism.

## Workflow

1. Run `git status --short`.
2. Check for already staged changes with `git diff --cached --name-only`.
3. If staged changes already exist, stop and tell the user this skill assumes a clean staging area before per-file sync.
4. Build the candidate list from the current status output.
5. Keep only paths ending in `.md`.
6. Record non-Markdown paths as skipped items.
7. If no Markdown candidates remain, report that there is nothing to sync and stop.

## Analyze Each File

Analyze each Markdown candidate independently.

- Modified tracked file: inspect `git diff -- <path>`.
- Added untracked file: read the file and summarize its topic, purpose, and major new sections.
- Deleted file: inspect git status and `git diff -- <path>` to summarize the removal.
- Renamed file: summarize the move and any content edits if both are present.
- Never combine multiple files into one summary.
- Write one concise summary per file in 1-3 sentences, focused on knowledge or content changes rather than line-level mechanics.

## Preview Before Sync

Before any `git add`, `git commit`, or `git push`, show a sync preview for every Markdown candidate in a consistent format:

- `文件路径`
- `状态`
- `同步摘要`
- `计划提交标题`

Also list skipped non-Markdown paths when present. Ask for confirmation before syncing. Do not commit anything before the user confirms.

## Commit Format

Commit one file at a time. Stage only the current file. Never use `git add .` or bundle multiple files into one commit.

Use the file stem as `<basename>`.

- Modified file: `obsidian: 更新 <basename>`
- New file: `obsidian: 新增 <basename>`
- Deleted file: `obsidian: 删除 <basename>`

Use this commit body exactly:

```text
文件: <relative-path>
摘要: <1-3 sentence summary>
```

## Sync Execution

After the user confirms, process candidates sequentially.

1. Stage only the current file.
2. Create the single-file commit with the planned title and summary body.
3. Check the branch state before pushing.
4. Push only when the branch can be pushed directly.
5. Report success for the file, then move to the next one.

## Push Safety Rules

- Do not run `git pull`, `git merge`, or `git rebase`.
- If git already shows the branch is behind, diverged, missing an upstream, or otherwise not ready for a direct push, stop and tell the user what needs manual attention.
- If `git push` fails for any file, stop immediately.
- After any stop condition, report:
  - completed files
  - the file that failed or was blocked
  - remaining files not yet synced

## Output Style

- Keep previews compact and easy to scan.
- Prefer Chinese when the user is writing in Chinese.
- Keep each file summary specific to the content of that file.
- When skipping files, explain that the default scope for this skill is Markdown notes only.

## Examples

Typical user requests that should follow this workflow:

- “帮我同步刚写完的 Obsidian 笔记”
- “检查当前 markdown 改动，逐文件生成摘要后同步”
- “把这次笔记修改提交并推送到远端”
