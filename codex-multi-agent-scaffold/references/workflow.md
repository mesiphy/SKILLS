# Multi-Agent Workflow Reference

## State flow

```text
planning / pending
  -> ready / pending
  -> developing / in-progress
  -> reviewing / done
  -> paused / review-pass
  -> ready / pending
  -> completed / review-pass
```

Failure flow:

```text
reviewing / done
  -> fixing / review-failed
  -> fixing / pending
  -> developing / in-progress
  -> reviewing / done
```

## Default read set for a new phase

Agents should read only:

- `.ai/rules.md`
- `.ai/project-context.md`
- `.ai/handoff/latest-summary.md`
- `.ai/active/action-plan.md`
- `.ai/active/status.md`
- `.ai/active/current-task/<current-task>.md`

They must not read `.ai/archive/**` unless the user explicitly asks for historical investigation.
