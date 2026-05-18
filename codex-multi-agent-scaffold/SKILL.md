---
name: codex-multi-agent-scaffold
description: Use when a user wants to create, initialize, or manage a file-driven multi-agent Codex development workflow for a software project, including .ai scaffolding, agent roles, task planning, development logs, reviews, status flow, phase archiving, and handoff summaries.
metadata:
  short-description: Scaffold a file-driven multi-agent Codex workflow
---

# Codex Multi-Agent Scaffold

Use this skill when the user wants to make multi-agent development the primary workflow for a project, initialize a reusable `.ai/` scaffold, or cleanly manage phases after dev-log/review history grows too large.

## Core idea

The workflow separates current execution state from historical records:

- `active/` is the current workbench.
- `archive/` is the historical record cabinet.
- `handoff/latest-summary.md` is the compact bridge into the next phase.

Agents must not default to reading archived history. They should work from the current status, current task, project context, and latest handoff summary.

## When initializing a project

1. Copy `assets/scaffold/.ai/` into the target project root.
2. Ask the planning agent to fill `project-context.md` from the repo.
3. Ask the planning agent to generate `active/action-plan.md`, `active/status.md`, and `active/current-task/*.md` from the user goal.
4. Run tasks through development, review, flow-control, and fix-planning agents.
5. At phase completion, archive `active/` outputs and generate `handoff/latest-summary.md`.

## Agent roles

- Orchestrator agent: reads `active/status.md`, chooses the next role, and pauses after every review.
- Planning agent: creates plans and tasks, but does not modify product code.
- Development agent: executes only the current task and writes dev-log.
- Review agent: reviews current task, diff, and dev-log; does not modify product code.
- Flow-control agent: advances only after review-pass and user confirmation.
- Fix-planning agent: creates focused fix tasks after failed review.
- Explorer agent: performs read-only analysis and may run in parallel.

## Safety defaults

- Never let multiple development agents implement different sequential tasks in parallel.
- Default to no automatic git commit.
- Pause after each review, even if review passed.
- Treat `rules.md > active/status.md > active/current-task > active/action-plan.md > project-context.md` as priority order.
- If a command, test, or build fails, record the failure instead of hiding it.
- If the agent must touch files outside the allowed task scope, record a `scope-exception` in dev-log.

## Included scaffold

The reusable file scaffold lives at:

```text
assets/scaffold/.ai/
```

It contains rules, templates, prompts, active/archive/handoff directories, and starter documents.
