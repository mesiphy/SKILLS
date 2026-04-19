---
name: git-obsidian-sync
description: Review and sync Obsidian or Markdown notes in a git repository. Use when Codex needs to inspect note changes, generate per-file commit summaries, and sync Markdown notes with Git in a Windows PowerShell environment. Follow a two-phase workflow: read-only preview first, then after one user confirmation run single-file git add/commit/push operations.
---

# Git Obsidian Sync

Use this skill to sync changed Obsidian notes with a confirmation-first Git workflow that fits Windows PowerShell and sandboxed command execution.

## Core Rules

1. Use a two-phase flow:
   - Phase 1: read-only inspection and preview
   - Phase 2: after one explicit user confirmation, execute `git add`, `git commit`, and `git push`
2. Keep the preview phase read-only. Do not stage, commit, or push before confirmation.
3. Stage only one Markdown file per commit. Never use `git add .`.
4. Default scope to Markdown notes only. Skip non-Markdown files and explain that they were excluded.
5. Prefer existing git commands and shell built-ins. Do not invent a separate sync mechanism.

## Phase 1: Read-Only Inspection

Run these checks first:

1. `git status --short`
2. `git diff --cached --name-only`
3. `git status -sb`

If `git diff --cached --name-only` is not empty, stop and tell the user this skill assumes a clean staging area before per-file sync.

If `git status -sb` shows the branch is `behind`, `diverged`, or otherwise not ready for a direct push, stop before any commit and report the problem.

If upstream details are needed in PowerShell, quote the revision literally:

```powershell
git rev-parse --abbrev-ref --symbolic-full-name '@{u}'
```

Do not use unquoted `@{u}` in PowerShell.

## Build Candidate List

Build candidates from `git status --short`.

- Keep paths ending in `.md`.
- Record non-Markdown paths as skipped items.
- If status output contains an untracked directory such as `?? notes/`, inspect only that directory to find Markdown files inside it.
- Do not recurse through the whole repository when a targeted directory scan is enough.
- If no Markdown candidates remain, report that there is nothing to sync and stop.

## Analyze Each Markdown File

Analyze each Markdown candidate independently.

- Modified tracked file: inspect `git diff -- <path>`.
- Added untracked file: read the file with UTF-8 and summarize its topic, purpose, and major sections.
- Deleted file: inspect `git diff -- <path>` and summarize the removal.
- Renamed file: summarize the move and any content edits if both are present.
- Never combine multiple files into one summary.
- Write one concise summary per file in 1-3 sentences, focused on knowledge or content changes rather than line-level mechanics.

When reading files in PowerShell, prefer UTF-8 explicitly:

```powershell
Get-Content -Encoding UTF8 -- <path>
```

## Preview Before Sync

Show one preview block per Markdown candidate with four fields in this order:

- path
- status
- summary
- planned commit title

Prefer Chinese field labels when the environment renders UTF-8 correctly. If terminal or tool output shows mojibake, fall back to ASCII labels such as `Path`, `Status`, `Summary`, and `Planned Commit Title`.

After the preview:

- list skipped non-Markdown paths when present
- remind the user that Markdown is the default sync scope
- ask for one confirmation before any write operation

Do not ask for additional workflow confirmation after the user has already confirmed. If the environment requests command approval for `git add`, `git commit`, or `git push`, treat that as an execution constraint rather than a second business-level confirmation.

## Commit Format

Commit one file at a time. Stage only the current file.

Use the file stem as `<basename>`.

Preferred commit titles:

- Modified file: `obsidian: 更新 <basename>`
- New file: `obsidian: 新增 <basename>`
- Deleted file: `obsidian: 删除 <basename>`
- Renamed file: `obsidian: 更新 <basename>`

If the environment cannot reliably preserve UTF-8 in command arguments, fall back to ASCII commit titles:

- Modified file: `obsidian: update <basename>`
- New file: `obsidian: add <basename>`
- Deleted file: `obsidian: delete <basename>`
- Renamed file: `obsidian: update <basename>`

Use this commit body exactly:

```text
Path: <relative-path>
Summary: <1-3 sentence summary>
```

## Phase 2: Sync Execution

After the user confirms, process candidates sequentially.

1. Stage only the current file with `git add -- <path>`.
2. Create the single-file commit with the planned title and summary body.
3. Re-check `git status -sb` before pushing.
4. Push only when the branch can be pushed directly.
5. Report success for the file, then continue to the next one.

If a write command fails because of sandbox or permission restrictions, request the minimum approval needed for that command and continue the same workflow after approval.

## Push Safety Rules

- Do not run `git pull`, `git merge`, or `git rebase`.
- If the branch is behind, diverged, missing an upstream, or otherwise not ready for a direct push, stop and tell the user what needs manual attention.
- If `git push` fails for any file, stop immediately.
- After any stop condition, report:
  - completed files
  - the file that failed or was blocked
  - remaining files not yet synced

## Output Style

- Prefer Chinese when the user is writing in Chinese.
- Keep previews compact and easy to scan.
- Keep each file summary specific to the content of that file.
- Mention the exact blocked command when permissions prevent automation.
- Use concrete file paths in status reports.

## Examples

Typical user requests that should trigger this skill:

- “帮我同步刚写完的 Obsidian 笔记”
- “检查当前 markdown 改动，逐文件生成摘要后同步”
- “把这次笔记修改提交并推送到远端”
