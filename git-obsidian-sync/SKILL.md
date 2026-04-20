---
name: git-obsidian-sync
description: Review and sync Obsidian or Markdown notes in a git repository. Use when the user asks to sync notes, commit recent Obsidian edits, push just-written Markdown files, or generate per-file commit summaries. This skill inspects current git changes, filters to Markdown note files, produces a compact preview, and then syncs one file at a time by default unless the user explicitly asks for preview-only behavior.
---

# Git Obsidian Sync

## Overview

Use this skill to turn changed Obsidian notes into a preview-first, auto-sync workflow.

- Prefer native git commands and built-in agent capabilities.
- Do not create helper scripts or invent a separate sync mechanism.
- Preserve the existing behavior:
  - inspect current changes
  - preview every Markdown file before syncing
  - commit one file at a time
  - push after each single-file commit
- Do not pause for a manual confirmation step unless the user explicitly asks to review first, preview only, or dry-run the sync.

## Platform And Shell Adaptation

Adapt commands to the current shell instead of assuming one platform.

- Resolve the repository root with `git rev-parse --show-toplevel` and run git commands from there.
- Use repo-relative paths in previews, commit bodies, and reports.
- If the current shell is PowerShell, use PowerShell-native quoting and control flow.
- If the current shell is a POSIX shell on macOS or Linux, use POSIX-safe quoting and `set -e` style failure handling.
- Do not hardcode Windows-only paths, `cmd.exe` syntax, or macOS-only shell syntax in the core workflow.

## Workflow

Keep discovery and preview read-only.

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
- Deleted file: inspect `git status --short` and `git diff -- <path>` to summarize the removal.
- Renamed file: summarize the move and any content edits if both are present.
- Never combine multiple files into one summary.
- Write one concise summary per file in 1-3 sentences, focused on knowledge or content changes rather than line-level mechanics.

## Preview Before Sync

Before any `git add`, `git commit`, or `git push`, show a sync preview for every Markdown candidate in a consistent format:

- `文件路径`
- `状态`
- `同步摘要`
- `计划提交标题`

Also list skipped non-Markdown paths when present. After showing the preview, continue directly to sync unless the user explicitly requested preview-only behavior, asked to review first, or the workflow hits a safety stop condition.

## Commit Format

Commit one file at a time. Stage only the current file. Never use `git add .` and never bundle multiple files into one commit.

Use the file stem as `<basename>`.

- Modified file: `obsidian: 更新 <basename>`
- New file: `obsidian: 新增 <basename>`
- Deleted file: `obsidian: 删除 <basename>`

Use this commit body exactly:

```text
文件: <relative-path>
摘要: <1-3 sentence summary>
```

## Approval Strategy

Minimize permission prompts without changing the workflow.

- Finish all read-only work first:
  - git status inspection
  - diff analysis
  - per-file summary generation
  - preview rendering
  - commit title and body planning
- Do not request elevated permissions during the preview phase.
- After rendering the preview, execute the sync immediately if the environment allows it.
- If git write or push operations are blocked by sandbox or are expected to require approval, do not ask for approval separately for each `git add`, `git commit`, or `git push`.
- Instead, request approval once for a single shell invocation that performs the full remaining sync sequence for all still-pending files.
- Pass the already-planned commit titles and bodies into that one invocation so the elevated step is execution-only, not analysis.
- If the environment supports reusable approval rules, prefer one narrowly scoped rule for the batch execution pattern in the current shell instead of several per-command approvals.
- Only fall back to multiple approvals if the environment makes a single execution approval impossible.
- If the user says `先预览`, `仅检查`, `dry-run`, or `不要提交`, stop after the preview and do not perform any git write operation.

## Sync Execution

After rendering the preview, process candidates sequentially and stop on the first failure.

1. Stage only the current file.
2. Create the single-file commit with the planned title and summary body.
3. Check the branch state before pushing that commit.
4. Push only when the branch can be pushed directly.
5. Report success for the file, then move to the next one.

When elevated execution is needed, keep the same sequence inside one shell invocation rather than spreading it across multiple approval requests.

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
- When approvals are needed, explain that the request is intentionally batched to reduce repeated prompts.

## Examples

Typical user requests that should follow this workflow:

- “帮我同步刚写完的 Obsidian 笔记”
- “检查当前 markdown 改动，逐文件生成摘要后同步”
- “把这次笔记修改提交并推送到远端”
- “先预览这次笔记改动，不要提交”
