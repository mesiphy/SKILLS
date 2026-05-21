---
name: codex-multi-agent-scaffold
description: Use when a user wants to create, initialize, or manage a file-driven multi-agent Codex development workflow for a software project, including .ai scaffolding, agent roles, task planning, development logs, reviews, status flow, phase archiving, and handoff summaries.
metadata:
  short-description: Scaffold a file-driven multi-agent Codex workflow
---

# Codex Multi-Agent Scaffold

Use this skill when the user wants to make multi-agent development the primary workflow for a project, initialize or update a reusable `.ai/` scaffold, generate project-specific agent context, validate workflow state, or manage phases after dev-log/review history grows too large.

## Core Mission

This skill is a multi-agent workflow generator, project adapter, and state validator.

It must help an agent:

1. Detect the target project root.
2. Create or update the project `AGENTS.md`, `.codex/agents/`, and `.ai/` scaffold.
3. Scan the target repository.
4. Generate verified `project-context.md` from real project evidence.
5. Generate project-specific rules from verified repository facts.
6. Initialize `active/action-plan.md`, `active/status.md`, `active/status.json`, and `active/current-task/*.md` when a development goal is provided.
7. Validate Codex entrypoints, agent configs, `.ai/` structure, and state before work proceeds.
8. Report initialization results, risks, unknowns, and next usage steps.

The workflow separates current execution state from historical records:

- `active/` is the current workbench.
- `archive/` is the historical record cabinet.
- `handoff/latest-summary.md` is the compact bridge into the next phase.

Agents must not default to reading archived history. They should work from `rules.md`, `project-context.md`, `project-specific-rules.md`, current status, current task, and latest handoff summary.

## Mode Selection

Before taking action, determine the current mode from the user's request and repository state.

- Use `init mode` when the user asks to initialize, create, set up, scaffold, or update multi-agent workflow files for a project.
- Use `plan mode` when the user provides a development goal and asks for planning, task breakdown, or action-plan generation.
- Use `run mode` when the user explicitly asks to execute the current task, review the current task, plan a fix, advance the workflow, or close/archive a phase.
- Use `validate mode` when the user asks to inspect the scaffold, check state, determine whether work can continue, or troubleshoot `.ai/` workflow files.
- If `.ai/` is missing and the user wants this skill applied to a project, start with `init mode`.
- If `.ai/` exists but required files are missing or inconsistent, use `validate mode` or `init mode` update behavior before planning or running.
- Do not move from planning into development without explicit user confirmation.

## Init Mode

Enter init mode when the user asks to initialize a multi-agent scaffold, create Codex workflow entrypoints, or make the current project support the workflow.

Required behavior:

1. Detect whether the current working directory is the target project root. Use repository evidence such as `.git/`, `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, README files, source directories, or user-provided paths.
2. Check whether `.ai/` already exists.
3. If workflow files do not exist, copy `assets/scaffold/` into the target project root so `AGENTS.md`, `.codex/agents/`, and `.ai/` are installed together.
4. If workflow files already exist, update conservatively: do not overwrite user content unless the user explicitly requests force behavior.
5. Scan the project and generate `.ai/repo-scan-report.md`.
6. Update `.ai/project-context.md` from verified facts in the scan report.
7. Generate `.ai/project-specific-rules.md` from verified project type, structure, commands, and risks.
8. Initialize `.ai/active/status.md` and `.ai/active/status.json`.
9. If the user already provided a development goal, generate `.ai/active/action-plan.md` and `.ai/active/current-task/*.md`; otherwise leave planning pending.
10. Run `.ai/` structure and state validation.
11. Output an initialization report with created, updated, skipped, and risky items.

Use these scripts when available:

```bash
python scripts/init_scaffold.py --target /path/to/project
python scripts/scan_project.py --target /path/to/project --output /path/to/project/.ai/repo-scan-report.md
python scripts/validate_ai_state.py --target /path/to/project
```

Init mode must not modify business code.

## Mandatory Outputs

When initializing or upgrading a repository, this skill must create or update:

1. `AGENTS.md`
2. `.codex/agents/orchestrator.toml`
3. `.codex/agents/planner.toml`
4. `.codex/agents/explorer.toml`
5. `.codex/agents/developer.toml`
6. `.codex/agents/reviewer.toml`
7. `.codex/agents/flow-controller.toml`
8. `.codex/agents/fix-planner.toml`
9. `.ai/rules.md`
10. `.ai/project-context.md`
11. `.ai/project-specific-rules.md`
12. `.ai/repo-scan-report.md`
13. `.ai/workflow-config.yaml`
14. `.ai/active/status.json`
15. `.ai/active/status.md`
16. `.ai/active/action-plan.md`
17. `.ai/templates/*`
18. `.ai/scripts/*`

Do not overwrite active logs, reviews, archive records, or user project files during conservative upgrades.

## Plan Mode

Enter plan mode when the user provides a development goal and wants task planning.

Required behavior:

1. Read `.ai/rules.md`.
2. Read `.ai/repo-scan-report.md` if present.
3. Read `.ai/project-context.md`.
4. Read `.ai/project-specific-rules.md`.
5. Read `.ai/active/status.json` first, then `.ai/active/status.md`.
6. Generate or update `.ai/active/action-plan.md`.
7. Split the plan into `.ai/active/current-task/*.md`.
8. Each task must include allowed scope, forbidden scope, acceptance criteria, required tests/checks, and expected outputs.
9. Update `.ai/active/status.md` and `.ai/active/status.json`.
10. Stop after the plan and wait for explicit user confirmation.

If critical project context is missing, create an explorer task or report the missing information instead of guessing.

Plan mode must not modify business code, create dev logs, create reviews, or start development.

## Run Mode

Enter run mode only when the user explicitly asks to execute or advance the current workflow state.

Role boundaries:

- Development agent only executes the task pointed to by `status.json.current_task_file`.
- Development agent must read `.ai/project-specific-rules.md`, list expected modified files before editing, stay within allowed scope, create a dev-log, update both status files, and run task-scope validation.
- Review agent only reviews the current task, dev-log, diff, acceptance criteria, tests, and scope compliance. It must not modify business code.
- Flow-control agent only advances after `task_status = review-pass` and explicit human confirmation recorded in status.
- Fix-planning agent only creates fix tasks after `review-failed` or `need-human-review`.
- Explorer agent performs read-only analysis and must not advance workflow state.
- Phase-close agent closes and archives a completed phase only after tasks are complete or explicitly waived.

Run mode must not automatically commit unless the user explicitly asks.

## Validate Mode

Enter validate mode when the user asks to check the scaffold, inspect status, verify whether work can continue, or diagnose workflow inconsistencies.

Required checks:

1. `.ai/` directory structure is complete.
2. `.ai/rules.md` exists.
3. `.ai/project-context.md` exists.
4. `.ai/project-specific-rules.md` exists.
5. `.ai/active/status.md` exists.
6. `.ai/active/status.json` exists.
7. `.ai/active/action-plan.md` exists.
8. `.ai/active/current-task/` exists and contains at least one task when a plan is active.
9. `status.json.current_task_file` exists when set.
10. `status.json.dev_log_file` exists when set.
11. `status.json.review_file` exists when set.
12. `phase` and `task_status` values belong to legal enums.
13. Codex entry files exist: `AGENTS.md`, `.codex/agents/*.toml`, `.ai/scripts/*.py`, and `.ai/workflow-config.yaml`.
14. Review-pass state has a review file.
15. Review-failed state has or requires a fix task.
16. Completed state has `active/final-report.md`.
17. `active/`, `archive/`, and `handoff/` directories exist.
18. `status.md` and `status.json` do not conflict.
19. No illegal task state conflict exists.

Use this script when available:

```bash
python scripts/validate_ai_state.py --target /path/to/project
```

Validation output must clearly separate `PASS`, `WARN`, and `FAIL`, and include concrete repair suggestions for failures.

## Agent roles

- Init scaffold agent: creates or updates `.ai/`, scans the project, generates verified context/rules, initializes status, and validates the result.
- Orchestrator agent: reads `active/status.json` first, chooses the next mode and role, and pauses after every review.
- Planning agent: creates plans and tasks, but does not modify product code.
- Development agent: executes only the current task and writes dev-log.
- Review agent: reviews current task, diff, and dev-log; does not modify product code.
- Flow-control agent: advances only after review-pass and user confirmation.
- Fix-planning agent: creates focused fix tasks after failed review.
- Explorer agent: performs read-only analysis and may run in parallel.
- Phase-close agent: creates final report, archives the phase, updates handoff, and does not modify product code.

## Safety defaults

- Never let multiple development agents implement different sequential tasks in parallel.
- Default to no automatic git commit.
- Pause after each review, even if review passed.
- Treat `AGENTS.md > rules.md > active/status.json > active/status.md > active/current-task > active/action-plan.md > project-specific-rules.md > project-context.md` as priority order.
- If a command, test, or build fails, record the failure instead of hiding it.
- If the agent must touch files outside the allowed task scope, stop and request user confirmation unless the task explicitly allows the change.
- Do not write assumptions as facts in `project-context.md` or `project-specific-rules.md`; unknown information belongs in an `Unknowns` section.
- User confirmation must be explicit and recorded before flow-control advances to the next task.
- Review, planning, validation, init, flow-control, and phase-close work must not modify business code.

## Included scaffold

The reusable file scaffold lives at:

```text
assets/scaffold/
```

It contains `AGENTS.md`, `.codex/agents/`, `.ai/rules.md`, templates, prompts, scripts, active/archive/handoff directories, and starter documents.

Deterministic helper scripts live in:

```text
scripts/
```

When scripts are unavailable, follow the same behavior manually and clearly report which checks could not be automated.
