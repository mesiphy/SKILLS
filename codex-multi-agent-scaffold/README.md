# Codex Multi-Agent Scaffold

`codex-multi-agent-scaffold` is a Codex skill for turning a software project into a file-driven multi-agent workflow.

It is no longer only a `.ai/` template. It is designed to act as:

- a multi-agent workflow generator
- a project-specific adapter
- a state validator

The skill helps Codex initialize `.ai/`, scan the repository, generate verified project context, create project-specific rules, plan work, execute one task at a time, review changes, control flow, and archive completed phases.

## Good Fits

Use this skill when you want:

- a disciplined planning/development/review workflow
- explicit human confirmation before task advancement
- current task state recorded in files
- dev logs and review files for every task
- project-specific rules derived from real repository evidence
- validation before continuing a multi-agent workflow
- phase handoff summaries after long development sessions

Avoid using it for tiny one-off edits where a normal single-agent change is simpler.

## Quick Start

In your target project root, ask Codex:

```text
Use the codex-multi-agent-scaffold skill to initialize this project.
Scan the repository, create the .ai scaffold, generate project-context.md,
project-specific-rules.md, status.md, status.json, and validate the result.
Do not modify business code.
```

Then provide your development goal:

```text
My development goal is:
...

Use planning mode to generate action-plan.md and current-task files.
Stop after the plan and wait for my confirmation.
```

After confirming the plan:

```text
Use development mode to execute the current task.
Follow .ai/active/status.json and the current-task file.
```

## Initialization

Initialization creates or updates the target project's `.ai/` directory.

Expected generated files include:

- `.ai/repo-scan-report.md`
- `.ai/project-context.md`
- `.ai/project-specific-rules.md`
- `.ai/active/status.md`
- `.ai/active/status.json`
- `.ai/active/action-plan.md`
- `.ai/active/current-task/*.md` when a development goal is provided

The initializer should not overwrite existing `.ai/` content unless you explicitly request force behavior.

You can also run the helper script directly from this skill directory:

```bash
python scripts/init_scaffold.py --target /path/to/project
python scripts/scan_project.py --target /path/to/project
python scripts/validate_ai_state.py --target /path/to/project
```

## Planning

Give Codex a development goal and ask for planning mode.

Planning mode must:

- read `.ai/rules.md`
- read `.ai/repo-scan-report.md`
- read `.ai/project-context.md`
- read `.ai/project-specific-rules.md`
- generate `.ai/active/action-plan.md`
- split work into `.ai/active/current-task/*.md`
- update `status.md` and `status.json`
- stop and wait for your confirmation

Each task should include allowed scope, forbidden scope, acceptance criteria, required checks, and expected outputs.

## Confirming The Plan

After reviewing the action plan, confirm explicitly:

```text
I confirm this action-plan. Proceed with the current task only.
```

Flow-control and development agents should not treat vague replies as confirmation.

## Executing The Current Task

Ask Codex:

```text
Use development mode to execute the current task from .ai/active/status.json.
Only modify files allowed by the current-task file.
Create the dev-log and run task scope validation.
Do not create review and do not commit.
```

The development agent should update:

- `.ai/active/dev-log/{task_id}-dev-log.md`
- `.ai/active/status.json`
- `.ai/active/status.md`

## Reviewing The Current Task

Ask Codex:

```text
Use review mode to review the current task.
Read the task, dev-log, project-specific-rules.md, and git diff.
Check allowed scope, acceptance criteria, and test evidence.
Write the review file only. Do not modify business code.
```

Review conclusions map to task status:

- `pass` -> `review-pass`
- `failed` -> `review-failed`
- `need-human-review` -> `need-human-review`

## Advancing To The Next Task

After a passing review, confirm explicitly:

```text
I confirm the review-pass result. Use flow-control mode to advance to the next pending task.
```

Flow-control mode should only advance when:

- the current task is `review-pass`
- a review file exists
- a dev-log exists
- your confirmation is explicit
- `status.json.last_human_confirmation` is updated

## Fixing A Failed Review

If review fails, ask:

```text
Use fix-planning mode to create a fix task from the failed review.
Do not modify business code.
Do not expand allowed scope unless I explicitly approve it.
```

Fix task naming:

- `.ai/active/current-task/001-fix-01-task.md`
- `.ai/active/dev-log/001-fix-01-dev-log.md`
- `.ai/active/review/001-fix-01-review.md`

## Archiving A Phase

When all tasks are complete and reviewed, ask:

```text
Use phase-close mode to generate final-report.md,
archive the active phase, update handoff/latest-summary.md,
and mark the phase completed.
Do not modify business code.
```

Phase-close mode should generate:

- `.ai/active/final-report.md`
- `.ai/archive/YYYY-MM-DD-{phase-name}/`
- `.ai/archive/YYYY-MM-DD-{phase-name}/status.final.md`
- `.ai/handoff/latest-summary.md`

## Validation

Use validation mode when the workflow feels stuck or inconsistent:

```text
Use validate mode to check the .ai scaffold and status.
Report PASS, WARN, FAIL, and suggested fixes.
```

Direct script:

```bash
python scripts/validate_ai_state.py --target /path/to/project
python scripts/validate_ai_state.py --target /path/to/project --strict
```

To validate development scope:

```bash
python scripts/validate_task_scope.py --target /path/to/project --task .ai/active/current-task/001-task.md
```

## File Layout

Key scaffold files:

- `.ai/rules.md`
- `.ai/repo-scan-report.md`
- `.ai/project-context.md`
- `.ai/project-specific-rules.md`
- `.ai/active/action-plan.md`
- `.ai/active/status.md`
- `.ai/active/status.json`
- `.ai/active/current-task/`
- `.ai/active/dev-log/`
- `.ai/active/review/`
- `.ai/archive/`
- `.ai/handoff/latest-summary.md`
- `.ai/templates/`
- `.ai/prompts/`

## Naming Rules

Normal task:

- `.ai/active/current-task/001-task.md`
- `.ai/active/dev-log/001-dev-log.md`
- `.ai/active/review/001-review.md`

Fix task:

- `.ai/active/current-task/001-fix-01-task.md`
- `.ai/active/dev-log/001-fix-01-dev-log.md`
- `.ai/active/review/001-fix-01-review.md`

## FAQ

### Does init mode modify business code?

No. Init mode should only create or update `.ai/` workflow files.

### What is the source of truth for state?

`status.json` is the machine-readable source of truth. `status.md` is the human-readable mirror. They must stay synchronized.

### What if project details are unknown?

Unknown information must stay in Unknowns until verified by files, commands, or explicit user confirmation.

### Can Codex commit automatically?

No. The workflow defaults to no automatic commit unless you explicitly request it.

### Can multiple development agents work in parallel?

Not on sequential tasks. Explorer agents may run in parallel because they are read-only.

## Current Limits

- The helper scripts initialize, scan, and validate state, but they do not run a full autonomous orchestrator.
- `project-context.md` and `project-specific-rules.md` still require agent judgment to turn scan evidence into clean prose.
- `status.md` and `status.json` synchronization is enforced by rules and validation, not by a centralized state-writing API.
- Scope validation depends on clear allowed scope entries in each task file.
- Complex monorepos may need manual project-root and command clarification.
