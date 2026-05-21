# AGENTS.md

This repository uses a file-driven multi-agent Codex workflow.

Before doing planning, coding, review, testing, flow-control, or phase-close work, read:

1. `.ai/rules.md`
2. `.ai/project-context.md`
3. `.ai/project-specific-rules.md`
4. `.ai/workflow-config.yaml` if it exists
5. `.ai/handoff/latest-summary.md`
6. `.ai/active/status.json` if it exists
7. `.ai/active/status.md`
8. `.ai/active/action-plan.md`
9. The current task file referenced by `.ai/active/status.json`

`.ai/rules.md` is the detailed workflow rule source. This file is the Codex project entrypoint.

Do not read `.ai/archive/**` unless the user explicitly asks for historical context.

Do not modify product code unless acting as the development agent on the current task.

Do not commit automatically.

After every review, pause unless `.ai/workflow-config.yaml` explicitly allows auto-advance.
