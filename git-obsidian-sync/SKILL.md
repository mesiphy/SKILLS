---
name: git-obsidian-sync
description: Review and sync Obsidian or Markdown notes in a git repository. Use when the user asks to sync notes, commit recent Obsidian edits, push just-written Markdown files, generate per-file commit summaries, sync current repository changes with Markdown files committed one at a time and non-Markdown files committed together, or explicitly says “检查gitignore文件” to find files that are ignored by .gitignore but still tracked and remove them from the git index. This skill inspects current git changes, applies the per-file Markdown sync workflow, and directly commits non-Markdown changes in a separate explicit commit unless the user asks for preview-only behavior.
---

# Git Obsidian Sync

## Overview

Use this skill to turn changed Obsidian notes and related repository changes into a preview-first sync workflow.

- Prefer native git commands and built-in agent capabilities.
- Do not create helper scripts or invent a separate sync mechanism.
- If the user explicitly says `检查gitignore文件`, run the Gitignore Tracked-File Cleanup workflow instead of the normal Markdown sync workflow.
- Preserve the Markdown behavior:
  - inspect current changes
  - preview every Markdown file before syncing
  - commit Markdown files one file at a time
  - push after each single-file commit
- Handle non-Markdown changes separately:
  - preview them before syncing
  - stage only explicit listed paths
  - commit them together in one direct commit
  - push after that direct commit
- Do not pause for a manual confirmation step unless the user explicitly asks to review first, preview only, or dry-run the sync.

## Platform And Shell Adaptation

Adapt commands to the current shell instead of assuming one platform.

- Resolve the repository root with `git rev-parse --show-toplevel` and run git commands from there.
- Use repo-relative paths in previews, commit bodies, and reports.
- If the current shell is PowerShell, use PowerShell-native quoting and control flow.
- If the current shell is a POSIX shell on macOS or Linux, use POSIX-safe quoting and `set -e` style failure handling.
- Do not hardcode Windows-only paths, `cmd.exe` syntax, or macOS-only shell syntax in the core workflow.

## Gitignore Tracked-File Cleanup

Use this workflow only when the user explicitly says `检查gitignore文件`. Do not run it for ordinary sync, commit, push, or preview requests.

Goal: find files that match `.gitignore` rules but are still tracked in git, then stop tracking them without deleting the local working-copy files.

Keep discovery read-only until the preview is shown.

1. Resolve the repository root with `git rev-parse --show-toplevel`.
2. Run `git status --short`.
3. Check for already staged changes with `git diff --cached --name-only`.
4. If staged changes already exist, stop and tell the user cleanup assumes a clean staging area.
5. Find ignored-but-tracked files with:

```sh
git ls-files -ci --exclude-standard
```

6. If the command returns no paths, report that no tracked files currently match `.gitignore` rules and stop.
7. Preview every candidate path and explain that cleanup will run `git rm --cached` so the file remains on disk but is removed from git tracking.
8. If the user requested `先预览`, `仅检查`, `dry-run`, or `不要提交`, stop after the preview.
9. Otherwise, run `git rm --cached -- <explicit paths>` for the candidate paths. Never use `git rm --cached .`.
10. Commit the index-removal changes with this title:

```text
chore: 停止跟踪 gitignore 文件
```

Use this body format:

```text
文件:
- <relative-path-1>
- <relative-path-2>

摘要: 清除已被 .gitignore 忽略但仍在 Git 索引中的文件，保留本地文件。
```

11. Push the commit only when the branch can be pushed directly according to the Push Safety Rules.

Do not delete working-copy files during this cleanup. Do not modify `.gitignore` unless the user explicitly asks to change ignore rules.

## Workflow

Keep discovery and preview read-only.

1. Run `git status --short`.
2. Check for already staged changes with `git diff --cached --name-only`.
3. If staged changes already exist, stop and tell the user this skill assumes a clean staging area before per-file sync.
4. Build the candidate list from the current status output.
5. Expand untracked directories into actual files with `git ls-files --others --exclude-standard` before classification.
6. Classify changed files into two groups:
   - Markdown candidates: paths ending in `.md`
   - Direct-commit candidates: changed files that do not end in `.md`
7. Do not discard direct-commit candidates. Record them for direct commit.
8. If neither group has candidates, report that there is nothing to sync and stop.

Classify by file path, not by directory name. Markdown files inside untracked folders still use the Markdown workflow.

## Analyze Each Markdown File

Analyze each Markdown candidate independently.

- Modified tracked file: inspect `git diff -- <path>`.
- Added untracked file: read the file and summarize its topic, purpose, and major new sections.
- Deleted file: inspect `git status --short` and `git diff -- <path>` to summarize the removal.
- Renamed file: summarize the move and any content edits if both are present.
- Never combine multiple Markdown files into one summary.
- Write one concise summary per Markdown file in 1-3 sentences, focused on knowledge or content changes rather than line-level mechanics.

## Direct-Commit Candidates

Non-Markdown files are not skipped by default.

- Do not generate detailed content summaries for non-Markdown files.
- Do not read large non-Markdown files unless needed for safety.
- Treat them as direct-commit candidates after preview.
- Stage only explicit listed paths. Never use `git add .`.

Stop and ask the user before syncing direct-commit candidates if they appear to include:

- secrets, credentials, tokens, private keys, or environment files
- large binaries or generated artifacts
- cache, build, dependency, or temporary directories
- files that are ignored by `.gitignore`
- any path whose purpose is unclear and may be risky to commit

## Preview Before Sync

Before any `git add`, `git commit`, or `git push`, show a sync preview for both groups.

For every Markdown candidate, use this format:

- `文件路径`
- `状态`
- `同步摘要`
- `计划提交标题`

For every direct-commit candidate, use this format:

- `文件路径`
- `状态`
- `处理方式`: direct commit, no content summary
- `计划提交标题`: `chore: 同步非 Markdown 文件`

Do not call non-Markdown files skipped unless they are intentionally excluded by gitignore or a safety rule.

After showing the preview, continue directly to sync unless the user explicitly requested preview-only behavior, asked to review first, or the workflow hits a safety stop condition.

## Markdown Commit Format

Commit Markdown files one file at a time. Stage only the current file. Never use `git add .` and never bundle multiple Markdown files into one commit.

Use the file stem as `<basename>`.

- Modified file: `obsidian: 更新 <basename>`
- New file: `obsidian: 新增 <basename>`
- Deleted file: `obsidian: 删除 <basename>`

Use this commit body exactly:

```text
文件: <relative-path>
摘要: <1-3 sentence summary>
```

## Direct Commit Format For Non-Markdown Files

After all Markdown candidates are synced, commit remaining direct-commit candidates together in one direct commit.

Use this title:

```text
chore: 同步非 Markdown 文件
```

Use this body format:

```text
文件:
- <relative-path-1>
- <relative-path-2>

摘要: 同步非 Markdown 文件变更。
```

Stage only the listed non-Markdown paths. Never use `git add .`.

If there are no direct-commit candidates, skip this step.

## Approval Strategy

Minimize permission prompts without changing the workflow.

- Finish all read-only work first:
  - git status inspection
  - staged-change inspection
  - candidate classification
  - untracked directory expansion
  - diff analysis
  - per-file summary generation
  - direct-commit candidate safety check
  - preview rendering
  - commit title and body planning
- Do not request elevated permissions during the preview phase.
- After rendering the preview, execute the sync immediately if the environment allows it.
- If git write or push operations are blocked by sandbox or are expected to require approval, do not ask for approval separately for each `git add`, `git commit`, or `git push`.
- Instead, request approval once for a single shell invocation that performs the full remaining sync sequence for all still-pending files.
- Pass the already-planned commit titles, bodies, and explicit path lists into that one invocation so the elevated step is execution-only, not analysis.
- If the environment supports reusable approval rules, prefer one narrowly scoped rule for the batch execution pattern in the current shell instead of several per-command approvals.
- Only fall back to multiple approvals if the environment makes a single execution approval impossible.
- If the user says `先预览`, `仅检查`, `dry-run`, or `不要提交`, stop after the preview and do not perform any git write operation.

## Sync Execution

After rendering the preview, process candidates sequentially and stop on the first failure.

1. Sync Markdown candidates first, preserving the existing one-file-at-a-time behavior.
2. For each Markdown candidate:
   - Check that the branch can be pushed directly.
   - Stage only the current Markdown file.
   - Create the single-file commit with the planned title and summary body.
   - Push the commit.
   - Report success for the file, then move to the next one.
3. After all Markdown sync completes, sync direct-commit candidates if any exist:
   - Check that the branch can be pushed directly.
   - Stage all direct-commit candidates by explicit path.
   - Create one direct commit with the planned non-Markdown title and body.
   - Push the commit.
4. Stop on the first failure and report completed files, failed or blocked files, and remaining files.

When elevated execution is needed, keep the same sequence inside one shell invocation rather than spreading it across multiple approval requests.

## Push Safety Rules

- Do not run `git pull`, `git merge`, or `git rebase`.
- If git already shows the branch is behind, diverged, missing an upstream, or otherwise not ready for a direct push, stop and tell the user what needs manual attention.
- If `git push` fails for any file or direct commit, stop immediately.
- After any stop condition, report:
  - completed Markdown files
  - completed direct-commit files
  - the file or commit that failed or was blocked
  - remaining files not yet synced

## Output Style

- Keep previews compact and easy to scan.
- Prefer Chinese when the user is writing in Chinese.
- Keep each Markdown file summary specific to the content of that file.
- For non-Markdown files, explain that they are being committed directly without content summaries.
- When files are excluded by safety rules, explain the specific reason.
- When approvals are needed, explain that the request is intentionally batched to reduce repeated prompts.

## Examples

Typical user requests that should follow this workflow:

- “帮我同步刚写完的 Obsidian 笔记”
- “检查当前 markdown 改动，逐文件生成摘要后同步”
- “把这次笔记修改提交并推送到远端”
- “把当前仓库同步，Markdown 保持逐文件摘要，其他文件直接提交”
- “先预览这次笔记改动，不要提交”
